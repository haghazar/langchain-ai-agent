from langchain_core.messages import HumanMessage, SystemMessage

from rag import create_llm
from tools import create_tools, get_tool_descriptions


ROUTING_SYSTEM_PROMPT = """
You are a tool-routing evaluator.

Your job is to select exactly one tool for the user's request.

Important:
- Use the tool descriptions as the source of truth.
- Do not rely only on tool names.
- If a tool is appropriate, call exactly one tool.
- Do not answer directly.
"""


GOLDEN_ROUTING_SET = [
    {
        "id": "R1",
        "question": "What is 18% of 2450?",
        "expected_tool": "calculator",
        "hard_case": False,
    },
    {
        "id": "R2",
        "question": "Who manages the Platform team?",
        "expected_tool": "get_team",
        "hard_case": False,
    },
    {
        "id": "R3",
        "question": "What is Sarah Kim's email?",
        "expected_tool": "get_employee",
        "hard_case": False,
    },
    {
        "id": "R4",
        "question": "According to our internal docs, what does the RAG checklist say about citations?",
        "expected_tool": "search_docs",
        "hard_case": False,
    },
    {
        "id": "R5",
        "question": "Search the web for public information about LangGraph checkpointing.",
        "expected_tool": "search_web",
        "hard_case": False,
    },
    {
        "id": "R6",
        "question": (
            "According to our internal docs, what is our checkpoint policy "
            "for customer-facing agent workflows?"
        ),
        "expected_tool": "search_docs",
        "hard_case": True,
    },
    {
        "id": "R7",
        "question": (
            "Find public web information about LangGraph checkpointing and interrupts."
        ),
        "expected_tool": "search_web",
        "hard_case": True,
    },
    {
        "id": "R8",
        "question": "What does our internal team directory say about the Platform team?",
        "expected_tool": "get_team",
        "hard_case": True,
    },
]


def get_first_tool_call(question: str, tools_mode: str):
    """
    Ask the LLM to choose one tool and return the first structured tool call.
    """

    tools = create_tools(mode=tools_mode)
    llm = create_llm()
    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content=ROUTING_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    ai_message = llm_with_tools.invoke(messages)
    tool_calls = getattr(ai_message, "tool_calls", [])

    if not tool_calls:
        return {
            "actual_tool": None,
            "tool_args": {},
        }

    first_tool_call = tool_calls[0]

    return {
        "actual_tool": first_tool_call["name"],
        "tool_args": first_tool_call["args"],
    }


def evaluate_routing(tools_mode: str = "fixed"):
    """
    Evaluate tool-selection accuracy on the golden routing set.
    """

    results = []

    for item in GOLDEN_ROUTING_SET:
        actual = get_first_tool_call(
            question=item["question"],
            tools_mode=tools_mode,
        )

        actual_tool = actual["actual_tool"]
        expected_tool = item["expected_tool"]

        result = {
            "id": item["id"],
            "question": item["question"],
            "expected_tool": expected_tool,
            "actual_tool": actual_tool,
            "tool_args": actual["tool_args"],
            "passed": actual_tool == expected_tool,
            "hard_case": item["hard_case"],
        }

        results.append(result)

    total = len(results)

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    accuracy = passed / total if total else 0

    return {
        "mode": tools_mode,
        "results": results,
        "passed": passed,
        "total": total,
        "accuracy": accuracy,
        "descriptions": get_tool_descriptions(tools_mode),
    }


def print_routing_report(evaluation):
    """
    Print one routing evaluation report.
    """

    print("=" * 100)
    print(f"ROUTING EVALUATION MODE: {evaluation['mode']}")
    print("=" * 100)

    for result in evaluation["results"]:
        print("-" * 100)
        print(f"ID: {result['id']}")
        print(f"Question: {result['question']}")
        print(f"Expected tool: {result['expected_tool']}")
        print(f"Actual tool: {result['actual_tool']}")
        print(f"Tool args: {result['tool_args']}")
        print(f"Hard case: {result['hard_case']}")
        print(f"Pass: {result['passed']}")

    print("=" * 100)
    print(
        f"Accuracy: {evaluation['passed']}/{evaluation['total']} "
        f"= {evaluation['accuracy']:.2f}"
    )
    print("=" * 100)
    print()


def evaluate_all_modes():
    """
    Run baseline → broken → fixed evaluation.
    """

    modes = ["baseline", "broken", "fixed"]
    evaluations = []

    for mode in modes:
        evaluation = evaluate_routing(tools_mode=mode)
        evaluations.append(evaluation)

    return evaluations


def main():
    evaluations = evaluate_all_modes()

    for evaluation in evaluations:
        print_routing_report(evaluation)


if __name__ == "__main__":
    main()