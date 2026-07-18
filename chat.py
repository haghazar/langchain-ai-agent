from agentwithtools import run_agent_with_history
from memory import ConversationMemory


class ChatSession:
    """
    Multi-turn chat session with memory.

    Every turn:
    1. assemble memory context
    2. inject it into agent
    3. run tool-calling agent
    4. save user + assistant turn back into memory
    """

    def __init__(self, tools_mode: str = "fixed", max_turns: int = 4):
        self.memory = ConversationMemory(max_turns=max_turns)
        self.tools_mode = tools_mode
        self.transcript = []

    def ask(self, user_message: str, verbose: bool = True):
        """
        Ask one question with memory.
        """

        assembled_context = self.memory.context()

        result = run_agent_with_history(
            question=user_message,
            assembled_context=assembled_context,
            tools_mode=self.tools_mode,
            verbose=verbose,
        )

        answer = result["answer"]
        trajectory = result["trajectory"]

        self.memory.add_turn(
            user_message=user_message,
            assistant_message=answer,
        )

        turn_log = {
            "user": user_message,
            "assembled_context": assembled_context,
            "trajectory": trajectory,
            "answer": answer,
        }

        self.transcript.append(turn_log)

        return turn_log


def run_memory_demo():
    """
    Step 3 demo:
    The follow-up works only with memory.
    """

    chat = ChatSession(tools_mode="fixed")

    first_turn = chat.ask(
        "Who manages the Platform team?",
        verbose=True,
    )

    print("\n" + "=" * 100)
    print("ASSEMBLED CONTEXT BEFORE SECOND TURN")
    print("=" * 100)
    print(chat.memory.context())
    print("=" * 100)

    second_turn = chat.ask(
        "And her email?",
        verbose=True,
    )

    return {
        "first_turn": first_turn,
        "second_turn": second_turn,
        "final_memory_context": chat.memory.context(),
    }


def run_integration_conversation():
    """
    Step 4 demo:
    One conversation that requires tool use, routing, and memory.
    """

    expected_tools = [
        "get_team",
        "get_employee",
        "calculator",
        "search_docs",
        "search_web",
    ]

    user_messages = [
        "Who manages the Platform team?",
        "And her email?",
        "What is 18% of 2450?",
        "According to our internal docs, what does the RAG checklist say about citations?",
        "Search the web for public information about LangGraph checkpointing.",
    ]

    memory_dependent_turns = {
        2,
    }

    chat = ChatSession(tools_mode="fixed")

    logs = []

    for turn_number, user_message in enumerate(user_messages, start=1):
        turn_log = chat.ask(
            user_message,
            verbose=True,
        )

        actual_tool = None

        if turn_log["trajectory"]:
            actual_tool = turn_log["trajectory"][0]["tool"]

        expected_tool = expected_tools[turn_number - 1]

        turn_log["turn_number"] = turn_number
        turn_log["expected_tool"] = expected_tool
        turn_log["actual_tool"] = actual_tool
        turn_log["routing_pass"] = actual_tool == expected_tool
        turn_log["memory_dependent"] = turn_number in memory_dependent_turns

        logs.append(turn_log)

    passed = sum(
        1
        for item in logs
        if item["routing_pass"]
    )

    total = len(logs)
    accuracy = passed / total if total else 0

    return {
        "logs": logs,
        "routing_accuracy": accuracy,
        "passed": passed,
        "total": total,
    }


def main():
    run_memory_demo()


if __name__ == "__main__":
    main()