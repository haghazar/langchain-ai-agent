from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from rag import create_llm
from tools import create_tools


SYSTEM_PROMPT = """
You are a multi-tool assistant.

You must use native structured tool calls when a tool is appropriate.

Important rules:
1. Select tools based on the tool descriptions. Tool descriptions are authoritative.
2. Do not hand-parse tool names from text.
3. If a user asks for math, use the calculator tool.
4. If a user asks about internal/private docs, use search_docs.
5. If a user asks about public web information, use search_web.
6. If a user asks about a person, use get_employee.
7. If a user asks about a team, use get_team.
8. If the user uses a pronoun like "her", "him", or "that" and no prior context is available,
   say you do not have enough context.
9. Keep final answers concise.
"""


def message_to_text(message):
    """
    Convert a LangChain message to plain text.
    """

    content = message.content

    if isinstance(content, str):
        return content.strip()

    return str(content).strip()


def make_tool_map(tools):
    """
    Convert tool list to dictionary by name.
    """

    return {
        current_tool.name: current_tool
        for current_tool in tools
    }


def run_agent(
    question: str,
    max_steps: int = 5,
    tools_mode: str = "fixed",
    verbose: bool = True,
):
    """
    Run the agent without memory.

    This is used to prove that follow-up questions fail when context is missing.
    """

    return run_agent_with_history(
        question=question,
        assembled_context="",
        max_steps=max_steps,
        tools_mode=tools_mode,
        verbose=verbose,
    )


def run_agent_with_history(
    question: str,
    assembled_context: str = "",
    max_steps: int = 5,
    tools_mode: str = "fixed",
    verbose: bool = True,
):
    """
    Run the agent with optional injected memory context.

    The assembled_context is what memory.py/chat.py injects every turn.
    """

    tools = create_tools(mode=tools_mode)
    tools_by_name = make_tool_map(tools)

    llm = create_llm()
    llm_with_tools = llm.bind_tools(tools)

    memory_block = assembled_context.strip()

    if memory_block:
        system_content = (
            SYSTEM_PROMPT
            + "\n\nConversation memory/context injected by the application:\n"
            + memory_block
        )
    else:
        system_content = SYSTEM_PROMPT

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=question),
    ]

    trajectory = []

    if verbose:
        print("=" * 100)
        print("AGENT RUN")
        print("=" * 100)
        print(f"Question: {question}")
        print(f"Tools mode: {tools_mode}")
        print("-" * 100)

    for step in range(1, max_steps + 1):
        ai_message = llm_with_tools.invoke(messages)
        messages.append(ai_message)

        tool_calls = getattr(ai_message, "tool_calls", [])

        if not tool_calls:
            answer = message_to_text(ai_message)

            if verbose:
                print("Final answer:")
                print(answer)
                print("=" * 100)

            return {
                "answer": answer,
                "trajectory": trajectory,
                "messages": messages,
            }

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            selected_tool = tools_by_name.get(tool_name)

            if selected_tool is None:
                observation = f"Unknown tool: {tool_name}"
            else:
                observation = selected_tool.invoke(tool_args)

            trajectory_row = {
                "step": step,
                "tool": tool_name,
                "args": tool_args,
                "observation": observation,
            }

            trajectory.append(trajectory_row)

            if verbose:
                print(f"Tool call: {trajectory_row}")

            messages.append(
                ToolMessage(
                    content=observation,
                    tool_call_id=tool_call_id,
                )
            )

    fallback_answer = "I could not complete the task within the max_steps limit."

    if verbose:
        print("Final answer:")
        print(fallback_answer)
        print("=" * 100)

    return {
        "answer": fallback_answer,
        "trajectory": trajectory,
        "messages": messages,
    }


def main():
    """
    Step 1 demo:
    Prove that calculator is selected via structured tool_call.
    """

    result = run_agent(
        "What is 18% of 2450?",
        tools_mode="fixed",
        verbose=True,
    )

    print()
    print("Trajectory:")
    for row in result["trajectory"]:
        print(row)

    print()
    print("Final answer:")
    print(result["answer"])


if __name__ == "__main__":
    main()