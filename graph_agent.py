import json
import operator
from typing import Literal

from typing_extensions import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

try:
    from langgraph.checkpoint.memory import InMemorySaver
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver as InMemorySaver

from rag import create_llm, create_retriever, format_documents


OUT_OF_DOMAIN_ANSWER = "I don't have information about that."


class AgentState(TypedDict, total=False):
    """
    State for the agentic RAG graph.

    messages:
        Thread-level chat history. This is how the graph remembers by thread.

    question:
        Current user question extracted from the latest HumanMessage.

    route:
        The graph's decision: retrieve or answer_directly.

    query:
        Current retrieval query. It may be rewritten if retrieval is not sufficient.

    context:
        Retrieved context from ChromaDB.

    retrieval_grade:
        Whether retrieved context is sufficient or insufficient.

    retry_count:
        Number of query rewrites/retrieval retries already attempted.

    max_retries:
        Maximum allowed retries.

    draft_answer:
        Draft answer before human approval.

    answer:
        Final approved answer.

    approved:
        Human approval result.

    human_feedback:
        Human feedback when draft is rejected.

    steps:
        Human-readable trace of graph decisions.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    question: str
    route: Literal["retrieve", "answer_directly"]
    query: str
    context: str
    retrieval_grade: Literal["sufficient", "insufficient"]
    retry_count: int
    max_retries: int
    draft_answer: str
    answer: str
    approved: bool
    human_feedback: str
    steps: Annotated[list[str], operator.add]


_LLM = None
_RETRIEVER = None


def get_llm():
    """
    Reuse the same project LLM from rag.py.
    """

    global _LLM

    if _LLM is None:
        _LLM = create_llm()

    return _LLM


def get_retriever():
    """
    Reuse the same project retriever from rag.py.
    """

    global _RETRIEVER

    if _RETRIEVER is None:
        _RETRIEVER = create_retriever()

    return _RETRIEVER


def message_to_text(message):
    """
    Convert a LangChain message content to plain text.
    """

    content = message.content

    if isinstance(content, str):
        return content.strip()

    return str(content).strip()


def get_latest_user_question(messages):
    """
    Find the latest HumanMessage in the thread.
    """

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message_to_text(message)

    return ""


def format_recent_history(messages, limit=8):
    """
    Format recent messages for prompts.

    This helps the graph answer thread-memory questions such as:
    "What was my previous question?"
    """

    recent_messages = messages[-limit:]
    lines = []

    for message in recent_messages:
        role = message.__class__.__name__.replace("Message", "")
        text = message_to_text(message)
        lines.append(f"{role}: {text}")

    return "\n".join(lines)


def parse_json_output(raw_output, fallback):
    """
    Parse LLM JSON output safely.

    If parsing fails, return fallback.
    """

    text = raw_output.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    start_index = text.find("{")
    end_index = text.rfind("}")

    if start_index != -1 and end_index != -1:
        text = text[start_index:end_index + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def call_llm_text(system_prompt, user_prompt):
    """
    Call the project LLM and return text content.
    """

    llm = get_llm()

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    return message_to_text(response)


def prepare_question_node(state: AgentState):
    """
    Prepare the current question and reset turn-specific fields.

    Because messages are stored by thread, this node extracts the latest user
    question from the message history.
    """

    messages = state.get("messages", [])
    question = get_latest_user_question(messages)

    max_retries = state.get("max_retries", 2)

    return {
        "question": question,
        "query": question,
        "context": "",
        "draft_answer": "",
        "answer": "",
        "retrieval_grade": "insufficient",
        "retry_count": 0,
        "max_retries": max_retries,
        "approved": False,
        "human_feedback": "",
        "steps": [
            f"prepare_question: current question='{question}'"
        ],
    }


def decide_route_node(state: AgentState):
    """
    Agentic decision #1:
    Decide whether to retrieve from the private RAG store or answer directly.

    This replaces the old blind retrieve -> answer pipeline.
    """

    system_prompt = """
You are a strict routing controller for an agentic RAG graph.

You must decide whether the graph should retrieve private context or answer directly.

Routes:
1. retrieve
Use this when the question is about:
- the private RAG document
- asset transfer
- chaincode
- private data collections
- buyer, seller, regulator
- ownership
- endorsement
- bid details
- anything likely stored in the user's private ChromaDB data

2. answer_directly
Use this only when:
- the user asks about the conversation history
- the user greets the assistant
- the user asks what the assistant can do
- the question can be answered from the chat history alone

Important:
- Do not answer the question.
- Return only JSON.
"""

    history = format_recent_history(state.get("messages", []))

    user_prompt = f"""
Current question:
{state["question"]}

Recent conversation history:
{history}

Return JSON exactly like this:
{{
  "route": "retrieve or answer_directly",
  "reason": "short reason"
}}
"""

    raw_output = call_llm_text(system_prompt, user_prompt)

    parsed = parse_json_output(
        raw_output,
        fallback={
            "route": "retrieve",
            "reason": "Fallback to retrieve because routing JSON failed.",
        },
    )

    route = parsed.get("route", "retrieve")

    if route not in ["retrieve", "answer_directly"]:
        route = "retrieve"

    reason = parsed.get("reason", "")

    return {
        "route": route,
        "steps": [
            f"decide_route: route={route}; reason={reason}"
        ],
    }


def retrieve_node(state: AgentState):
    """
    Retrieve context from ChromaDB using the current query.
    """

    retriever = get_retriever()

    query = state.get("query") or state["question"]
    documents = retriever.invoke(query)
    context = format_documents(documents)

    return {
        "context": context,
        "steps": [
            f"retrieve: query='{query}'; context_chars={len(context)}"
        ],
    }


def grade_retrieval_node(state: AgentState):
    """
    Agentic decision #2:
    Decide whether the retrieved context is sufficient to answer the question.
    """

    context = state.get("context", "")

    if not context.strip():
        return {
            "retrieval_grade": "insufficient",
            "steps": [
                "grade_retrieval: insufficient; reason=no context returned"
            ],
        }

    system_prompt = """
You are a strict retrieval grader.

Your job is to decide whether the retrieved context contains enough information
to answer the user's question.

Return only JSON.

Rules:
- sufficient = the context clearly contains the answer.
- insufficient = the context is missing the answer, is too vague, or only partially related.
- Do not answer the question.
"""

    user_prompt = f"""
Question:
{state["question"]}

Retrieved context:
{context}

Return JSON exactly like this:
{{
  "grade": "sufficient or insufficient",
  "reason": "short reason"
}}
"""

    raw_output = call_llm_text(system_prompt, user_prompt)

    parsed = parse_json_output(
        raw_output,
        fallback={
            "grade": "insufficient",
            "reason": "Fallback to insufficient because grading JSON failed.",
        },
    )

    grade = parsed.get("grade", "insufficient")

    if grade not in ["sufficient", "insufficient"]:
        grade = "insufficient"

    reason = parsed.get("reason", "")

    return {
        "retrieval_grade": grade,
        "steps": [
            f"grade_retrieval: grade={grade}; reason={reason}"
        ],
    }


def rewrite_query_node(state: AgentState):
    """
    Rewrite the retrieval query when retrieved context is not sufficient.
    """

    retry_count = state.get("retry_count", 0) + 1

    system_prompt = """
You rewrite search queries for a RAG retriever.

Goal:
Create a better retrieval query that is more likely to find the answer
in the private ChromaDB document store.

Rules:
- Keep the rewritten query concise.
- Preserve the user's intent.
- Use key domain terms if relevant.
- Return only the rewritten query text.
"""

    user_prompt = f"""
Original question:
{state["question"]}

Previous query:
{state.get("query", state["question"])}

Retrieved context was judged insufficient.

Rewrite the query:
"""

    rewritten_query = call_llm_text(system_prompt, user_prompt)

    if not rewritten_query:
        rewritten_query = state["question"]

    return {
        "query": rewritten_query,
        "retry_count": retry_count,
        "steps": [
            f"rewrite_query: retry_count={retry_count}; new_query='{rewritten_query}'"
        ],
    }


def draft_answer_node(state: AgentState):
    """
    Draft an answer.

    If context exists, answer only from context.
    If no context exists, answer only from conversation history.
    If neither contains the answer, return the out-of-domain message.
    """

    system_prompt = f"""
You are a strict answer generator for an agentic RAG graph.

Important rules:
1. If retrieved context is provided, answer only from that context.
2. If no retrieved context is provided, answer only from conversation history.
3. Do not use outside world knowledge.
4. If the answer is not explicitly supported by retrieved context or chat history,
   answer exactly:
"{OUT_OF_DOMAIN_ANSWER}"
5. Keep the answer concise.
"""

    history = format_recent_history(state.get("messages", []), limit=12)

    user_prompt = f"""
Question:
{state["question"]}

Route decision:
{state.get("route", "")}

Retrieved context:
{state.get("context", "")}

Recent conversation history:
{history}

Write the draft answer:
"""

    draft_answer = call_llm_text(system_prompt, user_prompt)

    if not draft_answer:
        draft_answer = OUT_OF_DOMAIN_ANSWER

    return {
        "draft_answer": draft_answer,
        "steps": [
            f"draft_answer: draft_chars={len(draft_answer)}"
        ],
    }


def human_approval_node(state: AgentState):
    """
    Pause the graph for human approval.

    This is the durable human-in-the-loop checkpoint.
    The graph stops here and resumes with Command(resume=...).
    """

    approval = interrupt(
        {
            "type": "human_approval_required",
            "question": state["question"],
            "draft_answer": state["draft_answer"],
            "instructions": (
                "Approve or reject the draft. "
                "Resume with {'approved': True} or "
                "{'approved': False, 'feedback': 'your feedback'}."
            ),
        }
    )

    approved = False
    feedback = ""

    if isinstance(approval, dict):
        approved = bool(approval.get("approved", False))
        feedback = approval.get("feedback", "")
    elif isinstance(approval, str):
        approved = approval.strip().lower() in ["approve", "approved", "yes", "y"]
        if not approved:
            feedback = approval

    if approved:
        return {
            "approved": True,
            "answer": state["draft_answer"],
            "human_feedback": "",
            "steps": [
                "human_approval: approved=True"
            ],
        }

    return {
        "approved": False,
        "human_feedback": feedback,
        "steps": [
            f"human_approval: approved=False; feedback='{feedback}'"
        ],
    }


def revise_answer_node(state: AgentState):
    """
    Revise the draft answer after human rejection.
    """

    feedback = state.get("human_feedback", "")

    system_prompt = f"""
You revise RAG answers based on human feedback.

Rules:
1. Do not add unsupported information.
2. If the requested revision cannot be supported by context or history,
   answer exactly:
"{OUT_OF_DOMAIN_ANSWER}"
3. Keep the revised answer concise.
"""

    history = format_recent_history(state.get("messages", []), limit=12)

    user_prompt = f"""
Question:
{state["question"]}

Retrieved context:
{state.get("context", "")}

Recent conversation history:
{history}

Previous draft:
{state.get("draft_answer", "")}

Human feedback:
{feedback}

Write a revised draft answer:
"""

    revised_answer = call_llm_text(system_prompt, user_prompt)

    if not revised_answer:
        revised_answer = OUT_OF_DOMAIN_ANSWER

    return {
        "draft_answer": revised_answer,
        "steps": [
            f"revise_answer: revised_chars={len(revised_answer)}"
        ],
    }


def finalize_node(state: AgentState):
    """
    Finalize the approved answer and store it in thread messages.

    Adding AIMessage to messages makes the answer part of thread memory.
    """

    answer = state.get("answer") or state.get("draft_answer") or OUT_OF_DOMAIN_ANSWER

    return {
        "answer": answer,
        "messages": [
            AIMessage(content=answer)
        ],
        "steps": [
            "finalize: final answer stored in thread messages"
        ],
    }


def route_after_decision(state: AgentState):
    """
    Conditional edge after route decision.
    """

    if state.get("route") == "answer_directly":
        return "draft_answer"

    return "retrieve"


def route_after_grading(state: AgentState):
    """
    Conditional edge after retrieval grading.

    If context is sufficient, answer.
    If context is insufficient and retries remain, rewrite query.
    If retries are exhausted, answer with whatever is available.
    """

    if state.get("retrieval_grade") == "sufficient":
        return "draft_answer"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if retry_count < max_retries:
        return "rewrite_query"

    return "draft_answer"


def route_after_approval(state: AgentState):
    """
    Conditional edge after human approval.
    """

    if state.get("approved"):
        return "finalize"

    return "revise_answer"


def build_graph():
    """
    Build and compile the agentic durable RAG graph.
    """

    workflow = StateGraph(AgentState)

    workflow.add_node("prepare_question", prepare_question_node)
    workflow.add_node("decide_route", decide_route_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_retrieval", grade_retrieval_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("draft_answer", draft_answer_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("revise_answer", revise_answer_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "prepare_question")
    workflow.add_edge("prepare_question", "decide_route")

    workflow.add_conditional_edges(
        "decide_route",
        route_after_decision,
        {
            "retrieve": "retrieve",
            "draft_answer": "draft_answer",
        },
    )

    workflow.add_edge("retrieve", "grade_retrieval")

    workflow.add_conditional_edges(
        "grade_retrieval",
        route_after_grading,
        {
            "draft_answer": "draft_answer",
            "rewrite_query": "rewrite_query",
        },
    )

    workflow.add_edge("rewrite_query", "retrieve")
    workflow.add_edge("draft_answer", "human_approval")

    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "finalize": "finalize",
            "revise_answer": "revise_answer",
        },
    )

    workflow.add_edge("revise_answer", "human_approval")
    workflow.add_edge("finalize", END)

    checkpointer = InMemorySaver()

    graph = workflow.compile(
        checkpointer=checkpointer
    )

    return graph


graph = build_graph()


def make_config(thread_id):
    """
    Create LangGraph config with thread_id.

    The thread_id is required for checkpointing and resume.
    """

    return {
        "configurable": {
            "thread_id": thread_id
        }
    }


def print_interrupts(result):
    """
    Print interrupt payloads, if any.
    """

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return

    print("=" * 100)
    print("GRAPH PAUSED FOR HUMAN APPROVAL")
    print("=" * 100)

    for item in interrupts:
        value = getattr(item, "value", item)
        print(value)

    print("=" * 100)
    print()


def ask_graph(question, thread_id="hayk-week4-thread", max_retries=2):
    """
    Start the graph with a user question.

    If the graph reaches human approval, it pauses and returns an interrupt.
    """

    config = make_config(thread_id)

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content=question)
            ],
            "max_retries": max_retries,
        },
        config=config,
    )

    print_interrupts(result)

    if "__interrupt__" not in result:
        print("Final answer:")
        print(result.get("answer", OUT_OF_DOMAIN_ANSWER))

    return result


def resume_graph(thread_id="hayk-week4-thread", approved=True, feedback=""):
    """
    Resume the graph after human approval interrupt.

    approved=True:
        accept the draft answer.

    approved=False:
        reject the draft and provide feedback.
    """

    config = make_config(thread_id)

    result = graph.invoke(
        Command(
            resume={
                "approved": approved,
                "feedback": feedback,
            }
        ),
        config=config,
    )

    print_interrupts(result)

    if "__interrupt__" not in result:
        print("Final answer:")
        print(result.get("answer", OUT_OF_DOMAIN_ANSWER))

    return result


def show_thread_state(thread_id="hayk-week4-thread"):
    """
    Inspect the latest checkpoint state for a thread.
    """

    config = make_config(thread_id)
    state = graph.get_state(config)

    print("=" * 100)
    print(f"THREAD STATE: {thread_id}")
    print("=" * 100)
    print(state.values)
    print("=" * 100)

    return state


def main():
    """
    Demo run.

    This will pause at human approval.
    Then it resumes with approval.
    """

    thread_id = "hayk-week4-demo"

    result = ask_graph(
        question="What does the chaincode verify before transferring the asset?",
        thread_id=thread_id,
        max_retries=2,
    )

    if "__interrupt__" in result:
        resume_graph(
            thread_id=thread_id,
            approved=True,
        )

    show_thread_state(thread_id)


if __name__ == "__main__":
    main()