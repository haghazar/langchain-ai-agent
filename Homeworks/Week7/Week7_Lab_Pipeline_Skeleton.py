"""
LAB: Your First Multi-Agent Pipeline
=====================================

Multi-agent topology:

    orchestrator -> parallel workers -> writer -> reviewer
                                               ^       |
                                               |       |
                                               +-------+

This file keeps the original lab shape, but implements all TODOs.
"""

import operator
import os
import sys
from pathlib import Path
from typing import Annotated, List, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field

MAX_REVISIONS = 2
_LLM = None


def add_project_root_to_path() -> None:
    """
    Find the project root by walking upward until config.py is found.

    This makes the file work even when it lives in:
        Homeworks/Week7/
    """

    current_file = Path(__file__).resolve()

    for parent in current_file.parents:
        if (parent / "config.py").exists():
            sys.path.insert(0, str(parent))
            return


add_project_root_to_path()


try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


CHAT_MODEL = "gemini-2.5-flash"


def require_api_key() -> str:
    """
    Read GOOGLE_API_KEY from .env or environment variables.
    """

    if load_dotenv is not None:
        load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise SystemExit(
            "GOOGLE_API_KEY not found. Add it to your .env file."
        )

    return api_key


MAX_REVISIONS = 2
_LLM = None


def get_llm():
    """
    Lazy LLM creation.

    This allows Week7_Lab_Selftest.py to import this module and test
    plain Python routing functions without spending model calls.
    """

    global _LLM

    if _LLM is None:
        _LLM = ChatGoogleGenerativeAI(
            model=CHAT_MODEL,
            temperature=0,
            google_api_key=require_api_key(),
        )

    return _LLM


# ---------------------------------------------------------------------------
# Provided: structured output schemas
# ---------------------------------------------------------------------------
class SubQuestions(BaseModel):
    sub_questions: List[str] = Field(
        description="2-4 focused, non-overlapping sub-questions"
    )


class ReviewVerdict(BaseModel):
    approved: bool
    feedback: str = Field(description="Empty string if approved")


# ---------------------------------------------------------------------------
# Provided: graph state
# ---------------------------------------------------------------------------
class State(TypedDict):
    question: str
    sub_questions: List[str]
    findings: Annotated[List[dict], operator.add]
    draft: str
    feedback: str
    revision_count: int
    approved: bool


class WorkerState(TypedDict):
    sub_question: str


def message_text(response) -> str:
    """
    Normalize LLM response content into text.
    """

    content = getattr(response, "content", None)

    if content is None:
        return str(response)

    if isinstance(content, str):
        return content

    return str(content)


def format_findings(findings: list[dict]) -> str:
    """
    Turn worker findings into a readable block for the writer.
    """

    if not findings:
        return "No findings were produced."

    blocks = []

    for index, finding in enumerate(findings, start=1):
        sub_question = finding.get("sub_question", "")
        answer = finding.get("answer", "")

        blocks.append(
            "\n".join(
                [
                    f"Finding {index}",
                    f"Sub-question: {sub_question}",
                    f"Answer: {answer}",
                ]
            )
        )

    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# TODO 1: orchestrator node
# ---------------------------------------------------------------------------
def orchestrator(state: State) -> dict:
    """
    Break the original question into 2-4 independent sub-questions.
    """

    question = state["question"]

    structured_llm = get_llm().with_structured_output(SubQuestions)

    prompt = f"""
You are the orchestrator in a multi-agent pipeline.

Break the user's question into 2-4 focused, independent, non-overlapping
sub-questions.

Rules:
- Each sub-question must be answerable by one worker.
- Do not include overlapping sub-questions.
- Do not answer the question.
- Return only the structured schema.

User question:
{question}
"""

    result = structured_llm.invoke(prompt)

    sub_questions = [
        item.strip()
        for item in result.sub_questions
        if item and item.strip()
    ]

    if not sub_questions:
        sub_questions = [question]

    return {
        "sub_questions": sub_questions,
        "findings": [],
    }


# ---------------------------------------------------------------------------
# TODO 2: assign_workers routing function
# ---------------------------------------------------------------------------
def assign_workers(state: State) -> list:
    """
    Fan out to one worker per sub-question.
    """

    sub_questions = state.get("sub_questions", [])

    return [
        Send(
            "worker",
            {
                "sub_question": sub_question,
            },
        )
        for sub_question in sub_questions
    ]


# ---------------------------------------------------------------------------
# TODO 3: worker node
# ---------------------------------------------------------------------------
def worker(state: WorkerState) -> dict:
    """
    Answer exactly one sub-question.

    The return shape is important:
        {"findings": [one_dict]}

    Because findings uses operator.add, parallel workers will be merged
    into one final list.
    """

    sub_question = state["sub_question"]

    prompt = f"""
You are a worker agent.

Answer exactly ONE sub-question.
Do not answer the original larger question.
Do not mention other workers.
Be concise but useful.

Sub-question:
{sub_question}
"""

    response = get_llm().invoke(prompt)
    answer = message_text(response).strip()

    return {
        "findings": [
            {
                "sub_question": sub_question,
                "answer": answer,
            }
        ]
    }


# ---------------------------------------------------------------------------
# TODO 4: writer node
# ---------------------------------------------------------------------------
def writer(state: State) -> dict:
    """
    Synthesize all worker findings into one draft.

    revision_count is incremented here only when the writer is producing
    a revision based on reviewer feedback.
    """

    question = state["question"]
    findings = state.get("findings", [])
    findings_text = format_findings(findings)

    feedback = state.get("feedback", "")
    draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)

    if feedback:
        revision_count += 1

        prompt = f"""
You are the writer agent in a multi-agent pipeline.

The reviewer rejected the previous draft.
Revise the draft using the reviewer's feedback and the worker findings.

Original question:
{question}

Worker findings:
{findings_text}

Previous draft:
{draft}

Reviewer feedback:
{feedback}

Write the revised report.
Make it clear, practical, and directly answer the original question.
"""

    else:
        prompt = f"""
You are the writer agent in a multi-agent pipeline.

Synthesize the worker findings into one clear report that answers the user's
original question.

Original question:
{question}

Worker findings:
{findings_text}

Write the first draft.
Make it clear, practical, and directly answer the original question.
"""

    response = get_llm().invoke(prompt)
    new_draft = message_text(response).strip()

    return {
        "draft": new_draft,
        "revision_count": revision_count,
    }


# ---------------------------------------------------------------------------
# TODO 5: reviewer node
# ---------------------------------------------------------------------------
def reviewer(state: State) -> dict:
    """
    Judge the draft against the original question.
    """

    question = state["question"]
    draft = state.get("draft", "")
    findings = state.get("findings", [])
    findings_text = format_findings(findings)

    structured_llm = get_llm().with_structured_output(ReviewVerdict)

    prompt = f"""
You are the reviewer agent in a multi-agent pipeline.

Judge whether the draft adequately answers the original question using the
available worker findings.

Approve the draft if:
- it directly answers the original question,
- it uses the worker findings,
- it is clear enough for a user,
- it does not introduce major unsupported claims.

If approved, return:
approved = true
feedback = ""

If rejected, return:
approved = false
feedback = concise, actionable revision instructions.

Original question:
{question}

Worker findings:
{findings_text}

Draft:
{draft}
"""

    verdict = structured_llm.invoke(prompt)

    if verdict.approved:
        feedback = ""
    else:
        feedback = verdict.feedback

    return {
        "approved": verdict.approved,
        "feedback": feedback,
    }


# ---------------------------------------------------------------------------
# TODO 6: route_after_review
# ---------------------------------------------------------------------------
def route_after_review(state: State) -> str:
    """
    Decide whether to revise or end.
    """

    approved = state.get("approved", False)
    revision_count = state.get("revision_count", 0)

    if approved:
        return "end"

    if revision_count >= MAX_REVISIONS:
        return "end"

    return "revise"


# ---------------------------------------------------------------------------
# TODO 7: build_graph
# ---------------------------------------------------------------------------
def build_graph():
    """
    Build and compile the LangGraph pipeline.
    """

    graph_builder = StateGraph(State)

    graph_builder.add_node("orchestrator", orchestrator)
    graph_builder.add_node("worker", worker)
    graph_builder.add_node("writer", writer)
    graph_builder.add_node("reviewer", reviewer)

    graph_builder.add_edge(START, "orchestrator")

    graph_builder.add_conditional_edges(
        "orchestrator",
        assign_workers,
        ["worker"],
    )

    graph_builder.add_edge("worker", "writer")
    graph_builder.add_edge("writer", "reviewer")

    graph_builder.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "revise": "writer",
            "end": END,
        },
    )

    return graph_builder.compile()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    graph = build_graph()

    if graph is None:
        raise SystemExit("build_graph() returned None - start with TODO 7's wiring.")

    result = graph.invoke(
        {
            "question": (
                "Should a small team put its accounting integrations behind "
                "one service or several?"
            ),
            "revision_count": 0,
        }
    )

    print(f"\nworkers that reported: {len(result.get('findings', []))}")
    print(
        f"revisions: {result.get('revision_count')}  "
        f"approved: {result.get('approved')}"
    )
    print(f"\n--- DRAFT ---\n{result.get('draft')}")