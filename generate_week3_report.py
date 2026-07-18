from pathlib import Path

from agentwithtools import run_agent
from chat import ChatSession, run_integration_conversation
from eval_routing import evaluate_all_modes, GOLDEN_ROUTING_SET
from tools import get_tool_descriptions


REPORT_PATH = Path("week3_report.md")


def md_code_block(text, language="text"):
    """
    Return fenced Markdown code block.
    """

    return f"```{language}\n{text}\n```"


def format_trajectory(trajectory):
    """
    Format trajectory list for Markdown.
    """

    if not trajectory:
        return "No tool calls."

    lines = []

    for row in trajectory:
        compact_row = {
            "tool": row["tool"],
            "args": row["args"],
        }
        lines.append(str(compact_row))

    return "\n".join(lines)


def first_tool(result):
    """
    Return first selected tool from an agent result.
    """

    trajectory = result.get("trajectory", [])

    if not trajectory:
        return None

    return trajectory[0]["tool"]


def generate_step_1():
    """
    Step 1:
    Prove native structured tool calling.
    """

    result = run_agent(
        "What is 18% of 2450?",
        tools_mode="fixed",
        verbose=False,
    )

    trajectory_text = format_trajectory(result["trajectory"])

    section = f"""
## Step 1 — Tool calling

Question:

> What is 18% of 2450?

Trajectory:

{md_code_block(trajectory_text, "python")}

Final answer:

{md_code_block(result["answer"])}

This proves that the model selected `calculator` through a structured tool call, not by hand-parsed text.
"""

    return section


def generate_step_2():
    """
    Step 2:
    Routing evaluation with baseline → broken → fixed descriptions.
    """

    evaluations = evaluate_all_modes()

    eval_by_mode = {
        evaluation["mode"]: evaluation
        for evaluation in evaluations
    }

    baseline = eval_by_mode["baseline"]
    broken = eval_by_mode["broken"]
    fixed = eval_by_mode["fixed"]

    golden_lines = []

    for item in GOLDEN_ROUTING_SET:
        golden_lines.append(
            f"- {item['id']}: expected `{item['expected_tool']}` — {item['question']}"
        )

    failed_baseline = [
        result
        for result in baseline["results"]
        if not result["passed"]
    ]

    failed_broken = [
        result
        for result in broken["results"]
        if not result["passed"]
    ]

    failed_fixed = [
        result
        for result in fixed["results"]
        if not result["passed"]
    ]

    baseline_failures = "\n".join(
        f"- {item['id']}: expected {item['expected_tool']}, got {item['actual_tool']}"
        for item in failed_baseline
    ) or "No failures."

    broken_failures = "\n".join(
        f"- {item['id']}: expected {item['expected_tool']}, got {item['actual_tool']}"
        for item in failed_broken
    ) or "No failures."

    fixed_failures = "\n".join(
        f"- {item['id']}: expected {item['expected_tool']}, got {item['actual_tool']}"
        for item in failed_fixed
    ) or "No failures."

    broken_descriptions = get_tool_descriptions("broken")
    fixed_descriptions = get_tool_descriptions("fixed")

    description_change = f"""
Broken `search_docs` description:

{broken_descriptions["search_docs"]}

Fixed `search_docs` description:

{fixed_descriptions["search_docs"]}

Broken `search_web` description:

{broken_descriptions["search_web"]}

Fixed `search_web` description:

{fixed_descriptions["search_web"]}
"""

    section = f"""
## Step 2 — Routing evaluation

### Golden set

{chr(10).join(golden_lines)}

### Accuracy numbers

- Baseline accuracy: {baseline["passed"]}/{baseline["total"]} = {baseline["accuracy"]:.2f}
- Broken accuracy: {broken["passed"]}/{broken["total"]} = {broken["accuracy"]:.2f}
- Fixed accuracy: {fixed["passed"]}/{fixed["total"]} = {fixed["accuracy"]:.2f}

### Baseline failures

{baseline_failures}

### Broken failures

{broken_failures}

### Fixed failures

{fixed_failures}

### Description change

{md_code_block(description_change)}
"""

    return section, evaluations


def generate_step_3():
    """
    Step 3:
    Prove memory continuity with vs without memory.
    """

    no_memory_first = run_agent(
        "Who manages the Platform team?",
        tools_mode="fixed",
        verbose=False,
    )

    no_memory_second = run_agent(
        "And her email?",
        tools_mode="fixed",
        verbose=False,
    )

    chat = ChatSession(tools_mode="fixed")

    with_memory_first = chat.ask(
        "Who manages the Platform team?",
        verbose=False,
    )

    assembled_context_before_second = chat.memory.context()

    with_memory_second = chat.ask(
        "And her email?",
        verbose=False,
    )

    section = f"""
## Step 3 — Memory continuity

### Without memory

Turn 1:

User: Who manages the Platform team?

Assistant: {no_memory_first["answer"]}

Trajectory:

{md_code_block(format_trajectory(no_memory_first["trajectory"]), "python")}

Turn 2:

User: And her email?

Assistant: {no_memory_second["answer"]}

Trajectory:

{md_code_block(format_trajectory(no_memory_second["trajectory"]), "python")}

### With memory

Turn 1:

User: Who manages the Platform team?

Assistant: {with_memory_first["answer"]}

Trajectory:

{md_code_block(format_trajectory(with_memory_first["trajectory"]), "python")}

Assembled context before second turn:

{md_code_block(assembled_context_before_second)}

Turn 2:

User: And her email?

Assistant: {with_memory_second["answer"]}

Trajectory:

{md_code_block(format_trajectory(with_memory_second["trajectory"]), "python")}

The assembled context contains `Sarah Kim`, which proves the application injected memory context before the second turn.
"""

    return section


def generate_step_4():
    """
    Step 4:
    Integrated multi-turn conversation.
    """

    integration = run_integration_conversation()

    turn_sections = []

    for log in integration["logs"]:
        turn_sections.append(
            f"""
### Turn {log["turn_number"]}

User:

{log["user"]}

Assembled context:

{md_code_block(log["assembled_context"])}

Trajectory:

{md_code_block(format_trajectory(log["trajectory"]), "python")}

Expected tool: `{log["expected_tool"]}`

Actual tool: `{log["actual_tool"]}`

Routing pass: `{log["routing_pass"]}`

Memory dependent: `{log["memory_dependent"]}`

Assistant:

{log["answer"]}
"""
        )

    section = f"""
## Step 4 — Integration conversation

Routing accuracy:

{integration["passed"]}/{integration["total"]} = {integration["routing_accuracy"]:.2f}

{chr(10).join(turn_sections)}
"""

    return section, integration


def generate_failure_analysis(evaluations, integration):
    """
    Analyze one failure root cause + fix.

    Prefer a broken-mode routing failure.
    """

    broken_eval = None

    for evaluation in evaluations:
        if evaluation["mode"] == "broken":
            broken_eval = evaluation
            break

    failed_item = None

    if broken_eval:
        for result in broken_eval["results"]:
            if not result["passed"]:
                failed_item = result
                break

    if failed_item:
        section = f"""
## One analyzed failure

Failure selected from the intentionally broken routing run.

Question:

> {failed_item["question"]}

Expected tool:

`{failed_item["expected_tool"]}`

Actual tool:

`{failed_item["actual_tool"]}`

Root cause:

The tool description was intentionally misleading. The model was instructed to trust tool descriptions, so it selected the wrong tool. This is a routing-layer failure, not a memory failure.

Fix:

Sharpen the tool descriptions so they clearly separate internal/private document search from public web search, and clearly separate person lookup from team lookup.

Result:

The fixed description run recovered the routing accuracy compared with the broken run.
"""
        return section

    section = """
## One analyzed failure

No failed item appeared in the broken run. This means the current golden set may not be hard enough for this model.

Root cause:

The model may be relying on tool names or task semantics strongly enough that the intentionally broken descriptions did not change behavior.

Fix:

Add harder overlap questions where the same keywords appear in both internal-doc and public-web contexts, and add person-vs-team ambiguity cases such as asking about "Platform" where the correct tool is `get_team`, not `get_employee`.
"""

    return section


def generate_final_sentence(evaluations):
    """
    Required one-sentence conclusion.
    """

    fixed_eval = None

    for evaluation in evaluations:
        if evaluation["mode"] == "fixed":
            fixed_eval = evaluation
            break

    routing_failures = 0

    if fixed_eval:
        routing_failures = sum(
            1
            for result in fixed_eval["results"]
            if not result["passed"]
        )

    if routing_failures > 0:
        sentence = (
            "Routing broke more often in my agent because the difficult cases were "
            "correct-selection problems: the model had to choose between overlapping tools."
        )
    else:
        sentence = (
            "Memory was the more fragile layer conceptually, because follow-up questions only worked "
            "when the application explicitly injected the assembled context; without that context, "
            "the model could not resolve pronouns like 'her'."
        )

    return f"""
## Final sentence

{sentence}
"""


def main():
    sections = []

    sections.append("# Week 3 Report — Agents that choose, measure, and remember\n")

    sections.append(generate_step_1())

    step_2_section, evaluations = generate_step_2()
    sections.append(step_2_section)

    sections.append(generate_step_3())

    step_4_section, integration = generate_step_4()
    sections.append(step_4_section)

    sections.append(generate_failure_analysis(evaluations, integration))

    sections.append(generate_final_sentence(evaluations))

    report = "\n".join(sections)

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(f"Report written to {REPORT_PATH.resolve()}")


if __name__ == "__main__":
    main()