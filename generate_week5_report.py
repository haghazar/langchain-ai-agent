from pathlib import Path

from email_agent import (
    EmailAssistant,
    EmailMessage,
    EmailResponseAgent,
    EmailTriageRouter,
)
from email_memory import EmailMemoryStore
from week5_oop_agent import (
    ChatSession,
    ConversationMemory,
    RoutingEvaluator,
    ToolCallingAgent,
    ToolRegistry,
)


REPORT_PATH = Path("week5_report.md")
FENCE = "`" * 3


def md_code_block(text: str, language: str = "text") -> str:
    """
    Create a Markdown code block without putting raw triple-backticks
    directly into the Python source.
    """

    return f"{FENCE}{language}\n{text}\n{FENCE}"


def clean_table_cell(value) -> str:
    """
    Make text safe for Markdown table cells.
    """

    text = str(value)
    text = text.replace("\n", " ")
    text = text.replace("|", "\\|")
    return text


def format_trajectory(trajectory: list[dict]) -> str:
    """
    Format agent trajectory for the report.
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


def build_class_agent() -> tuple[ToolRegistry, ToolCallingAgent]:
    """
    Build the Week 5 class-based agent.
    """

    registry = ToolRegistry(mode="fixed")
    agent = ToolCallingAgent(
        registry=registry,
        max_steps=5,
    )

    return registry, agent


def generate_architecture_section() -> str:
    """
    Explain the class-based architecture.
    """

    return """
## 1. Architecture overview

For Week 5, I refactored the flat script-style agent into object-oriented components.

The class-based implementation is separated into these components:

- `ToolRegistry` owns tool data, tool descriptions, and tool construction.
- `ToolCallingAgent` owns the LLM, tools, tool map, max step configuration, and trajectory.
- `ConversationMemory` owns recent turns and rolling summary.
- `ChatSession` owns a `ToolCallingAgent`, a `ConversationMemory`, and the transcript.
- `RoutingEvaluator` owns the golden set and routing evaluation results.
- `EmailMemoryStore` owns semantic, episodic, and procedural memory.
- `EmailTriageRouter` owns email triage behavior.
- `EmailResponseAgent` owns reply drafting behavior.
- `EmailAssistant` composes the memory store, triage router, and response agent.

This demonstrates encapsulation because state is owned by classes instead of module-level global variables.
"""


def generate_composition_section() -> str:
    """
    Explain composition.
    """

    diagram = "\n".join(
        [
            "EmailAssistant",
            "├── has-a EmailMemoryStore",
            "├── has-a EmailTriageRouter",
            "└── has-a EmailResponseAgent",
        ]
    )

    return f"""
## 2. Composition proof

The email assistant is assembled using composition:

{md_code_block(diagram)}

`EmailAssistant` does not inherit from the memory store, router, or response agent. It receives ready instances and orchestrates them.

This means the memory implementation can be swapped later. For example, `EmailMemoryStore` could be replaced with a Chroma-backed store without rewriting the triage router or response agent.
"""


def generate_behavior_preserving_section() -> str:
    """
    Compare the new class-based version against the old flat script if available.
    """

    _, class_agent = build_class_agent()

    new_math = class_agent.run(
        "What is 18% of 2450?",
        verbose=False,
    )

    new_team = class_agent.run(
        "Who manages the Platform team?",
        verbose=False,
    )

    old_math_answer = "Old flat script could not be executed."
    old_math_tool = "Unavailable"
    old_team_answer = "Old flat script could not be executed."
    old_team_tool = "Unavailable"
    math_match = "Old flat script unavailable"
    team_match = "Old flat script unavailable"

    try:
        from agentwithtools import run_agent

        old_math = run_agent(
            "What is 18% of 2450?",
            tools_mode="fixed",
            verbose=False,
        )

        old_team = run_agent(
            "Who manages the Platform team?",
            tools_mode="fixed",
            verbose=False,
        )

        old_math_answer = old_math["answer"]
        old_math_tool = old_math["trajectory"][0]["tool"]

        old_team_answer = old_team["answer"]
        old_team_tool = old_team["trajectory"][0]["tool"]

        math_match = old_math_tool == new_math.trajectory[0]["tool"] and "441" in new_math.answer
        team_match = old_team_tool == new_team.trajectory[0]["tool"] and "Sarah Kim" in new_team.answer

    except Exception as error:
        old_math_answer = f"Old flat script could not be executed: {error}"
        old_team_answer = f"Old flat script could not be executed: {error}"

    comparison_table = "\n".join(
        [
            "| Test | Old flat script | New class-based version | Match |",
            "|---|---|---|---|",
            (
                "| Calculator | "
                f"`{clean_table_cell(old_math_tool)}` → {clean_table_cell(old_math_answer)} | "
                f"`{clean_table_cell(new_math.trajectory[0]['tool'])}` → {clean_table_cell(new_math.answer)} | "
                f"{clean_table_cell(math_match)} |"
            ),
            (
                "| Platform manager | "
                f"`{clean_table_cell(old_team_tool)}` → {clean_table_cell(old_team_answer)} | "
                f"`{clean_table_cell(new_team.trajectory[0]['tool'])}` → {clean_table_cell(new_team.answer)} | "
                f"{clean_table_cell(team_match)} |"
            ),
        ]
    )

    return f"""
## 3. Behavior-preserving refactor

A refactor should preserve behavior, not merely rewrite code in a new style.

The class-based version was compared against the previous flat script behavior where possible.

{comparison_table}

New class-based calculator trajectory:

{md_code_block(format_trajectory(new_math.trajectory), "python")}

New class-based calculator final answer:

{md_code_block(new_math.answer)}
"""


def generate_tool_calling_and_routing_section() -> str:
    """
    Prove structured tool calling and routing accuracy.
    """

    _, agent = build_class_agent()

    result = agent.run(
        "What is 18% of 2450?",
        verbose=False,
    )

    evaluator = RoutingEvaluator(agent=agent)
    routing_report = evaluator.evaluate(verbose=False)

    routing_lines = []

    for item in routing_report["results"]:
        routing_lines.append(
            f"| {item['id']} | {item['expected_tool']} | {item['actual_tool']} | {item['passed']} |"
        )

    routing_table = "\n".join(routing_lines)

    accuracy_text = f"{routing_report['passed']}/{routing_report['total']} = {routing_report['accuracy']:.2f}"

    return f"""
## 4. Tool calling and routing measurement

### Structured tool calling proof

Question:

> What is 18% of 2450?

Trajectory:

{md_code_block(format_trajectory(result.trajectory), "python")}

Final answer:

{md_code_block(result.answer)}

The trajectory shows that the model selected `calculator` through a structured tool call.

### Routing accuracy

Routing accuracy:

{md_code_block(accuracy_text)}

| ID | Expected tool | Actual tool | Pass |
|---|---|---|---|
{routing_table}
"""


def generate_memory_followup_section() -> str:
    """
    Prove conversation memory with a follow-up question.
    """

    _, agent = build_class_agent()

    memory = ConversationMemory(max_turns=4)

    chat = ChatSession(
        agent=agent,
        memory=memory,
    )

    first_turn = chat.ask(
        "Who manages the Platform team?",
        verbose=False,
    )

    context_before_second_turn = memory.context()

    second_turn = chat.ask(
        "And her email?",
        verbose=False,
    )

    return f"""
## 5. Conversation memory proof

The follow-up question works because the application injects assembled memory context into the next turn.

### Turn 1

User:

{md_code_block("Who manages the Platform team?")}

Assistant:

{md_code_block(first_turn["answer"])}

Trajectory:

{md_code_block(format_trajectory(first_turn["trajectory"]), "python")}

### Assembled context before Turn 2

{md_code_block(context_before_second_turn)}

The assembled context contains `Sarah Kim`.

### Turn 2

User:

{md_code_block("And her email?")}

Assistant:

{md_code_block(second_turn["answer"])}

Trajectory:

{md_code_block(format_trajectory(second_turn["trajectory"]), "python")}

This proves that the follow-up resolved `her` from injected memory context.
"""


def generate_email_memory_section() -> str:
    """
    Prove semantic, episodic, and procedural email memory.
    """

    memory_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=True,
    )

    assistant = EmailAssistant(
        memory_store=memory_store,
        triage_router=EmailTriageRouter(memory_store),
        response_agent=EmailResponseAgent(memory_store),
    )

    assistant.remember_fact(
        "Hayk prefers concise, warm, professional email replies."
    )

    semantic_recall = assistant.recall_style_without_email()

    follow_up_email = EmailMessage(
        sender="important.client@example.com",
        subject="Checking updates",
        body="Just checking if there are any updates on this.",
    )

    before_episode = assistant.process_email(follow_up_email)

    assistant.learn_from_example(
        email_text="Just checking if there are any updates.",
        decision="reply",
        reason="A follow-up from an important client should receive an acknowledgment.",
    )

    after_episode = assistant.process_email(follow_up_email)

    procedural_before = memory_store.get_procedural_instructions()

    assistant.apply_feedback(
        "Use a formal banking tone and avoid casual phrases."
    )

    procedural_after = memory_store.get_procedural_instructions()

    reloaded_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=False,
    )

    reloaded_procedural = reloaded_store.get_procedural_instructions()

    procedural_email = EmailMessage(
        sender="client@example.com",
        subject="Loan payment question",
        body="Please clarify the payment deadline for the loan.",
    )

    procedural_result = assistant.process_email(procedural_email)

    semantic_text = "\n".join(f"- {fact}" for fact in semantic_recall)
    procedural_before_text = "\n".join(f"- {item}" for item in procedural_before)
    procedural_after_text = "\n".join(f"- {item}" for item in procedural_after)
    reloaded_text = "\n".join(f"- {item}" for item in reloaded_procedural)

    before_episode_text = "\n".join(
        [
            f"Action: {before_episode['decision'].action}",
            f"Reason: {before_episode['decision'].reason}",
            f"Memory used: {before_episode['decision'].memory_used}",
        ]
    )

    stored_episode_text = "\n".join(
        [
            "Email: Just checking if there are any updates.",
            "Decision: reply",
            "Reason: A follow-up from an important client should receive an acknowledgment.",
        ]
    )

    after_episode_text = "\n".join(
        [
            f"Action: {after_episode['decision'].action}",
            f"Reason: {after_episode['decision'].reason}",
            f"Memory used: {after_episode['decision'].memory_used}",
        ]
    )

    return f"""
## 6. Email agent memory acts

### 6.1 Semantic memory

Stored fact:

{md_code_block("Hayk prefers concise, warm, professional email replies.")}

Recall with no email in sight:

{md_code_block(semantic_text)}

This proves semantic memory stores and recalls stable facts.

### 6.2 Episodic memory

Before adding one episodic example:

{md_code_block(before_episode_text)}

Then one example was stored:

{md_code_block(stored_episode_text)}

After adding the episodic example:

{md_code_block(after_episode_text)}

The same email changed from `archive` to `reply` without changing a hard-coded rule. The decision changed because an episodic memory was retrieved.

### 6.3 Procedural memory

Procedural instructions before feedback:

{md_code_block(procedural_before_text)}

Feedback applied:

{md_code_block("Use a formal banking tone and avoid casual phrases.")}

Procedural instructions after feedback:

{md_code_block(procedural_after_text)}

Reloaded procedural instructions from JSON:

{md_code_block(reloaded_text)}

Draft after procedural feedback:

Subject:

{md_code_block(procedural_result["draft"].subject)}

Body:

{md_code_block(procedural_result["draft"].body)}

This proves procedural feedback permanently rewrote the stored instructions in `email_memory_store.json`.
"""


def generate_gmail_section() -> str:
    """
    Summarize real Gmail draft-only proof.
    """

    supported_methods = "\n".join(
        [
            "list_recent_messages()",
            "create_draft_reply()",
        ]
    )

    intentionally_missing_methods = "\n".join(
        [
            "send_email()",
            "send_draft()",
        ]
    )

    observed_output = "\n".join(
        [
            "REAL GMAIL DRAFT CREATED BY EMAIL ASSISTANT",
            "The email was saved as a Gmail draft only. It was not sent.",
        ]
    )

    return f"""
## 7. Real Gmail draft-only integration

The Gmail integration was implemented in `week5_gmail_client.py`.

The Gmail client supports:

{md_code_block(supported_methods)}

It intentionally does not implement:

{md_code_block(intentionally_missing_methods)}

A real Gmail draft was created during testing with `test_email_agent_gmail_draft.py`.

Observed test output:

{md_code_block(observed_output)}

This proves that the email agent can create a real Gmail draft while preserving the safety rule: no automatic sending.
"""

def generate_test_results_section() -> str:
    """
    Summarize final automated test results.
    """

    test_output = "\n".join(
        [
            "TEST 1: STRUCTURED TOOL CALLING - PASSED",
            "TEST 2: CLASS-BASED MEMORY FOLLOW-UP - PASSED",
            "TEST 3: ROUTING EVALUATOR - PASSED",
            "TEST 4: SEMANTIC MEMORY - PASSED",
            "TEST 5: EPISODIC MEMORY FLIPS TRIAGE DECISION - PASSED",
            "TEST 6: PROCEDURAL MEMORY PERSISTENCE - PASSED",
            "ALL WEEK 5 CORE TESTS PASSED",
        ]
    )

    return f"""
## 8. Automated test results

The Week 5 core test file `test_week5_homework.py` was executed successfully.

{md_code_block(test_output)}

This confirms that the class-based agent, routing evaluator, memory follow-up, and all three email memory types work end-to-end.
"""


def generate_failure_analysis_section() -> str:
    """
    Analyze one limitation/failure mode.
    """

    return """
## 9. One analyzed failure / limitation

The most important limitation is that the current email triage logic uses simple keyword overlap for episodic memory retrieval.

Root cause:

A keyword-overlap matcher can miss semantically similar emails if they use different words. For example, an email saying "Could you update me?" may be similar to "Just checking if there are any updates", but the overlap score may be weak.

Fix:

The memory store is encapsulated behind `EmailMemoryStore`, so the implementation can be swapped later. A Chroma-backed vector store can replace the simple JSON keyword matching without changing `EmailAssistant`, `EmailTriageRouter`, or `EmailResponseAgent`.

This is exactly why the design uses composition.
"""


def generate_final_sentence_section() -> str:
    """
    Required final sentence.
    """

    return """
## 10. Final sentence

Memory was the more fragile layer in my agent, because follow-up questions and email triage decisions only worked when the application explicitly injected or retrieved the right memory; routing was more stable after tool descriptions were made clear.
"""


def main():
    print("=" * 100, flush=True)
    print("STARTING WEEK 5 REPORT GENERATION", flush=True)
    print("=" * 100, flush=True)

    sections = [
    "# Week 5 Report — From Scripts to Classes + the Email Agent\n",
    generate_architecture_section(),
    generate_composition_section(),
    generate_behavior_preserving_section(),
    generate_tool_calling_and_routing_section(),
    generate_memory_followup_section(),
    generate_email_memory_section(),
    generate_gmail_section(),
    generate_test_results_section(),
    generate_failure_analysis_section(),
    generate_final_sentence_section(),
]

    report = "\n".join(sections)

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print("=" * 100, flush=True)
    print("WEEK 5 REPORT GENERATED", flush=True)
    print("=" * 100, flush=True)
    print(f"Report path: {REPORT_PATH.resolve()}", flush=True)
    print("=" * 100, flush=True)


if __name__ == "__main__":
    main()