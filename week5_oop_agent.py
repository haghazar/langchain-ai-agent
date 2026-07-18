import ast
import operator
import re
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool

from rag import create_llm


class ToolRegistry:
    """
    Class-based tool registry.

    This class owns:
    - internal document data
    - mock web data
    - employee data
    - team data
    - tool descriptions
    - tool construction

    There are no module-level tool globals.
    """

    def __init__(self, mode: str = "fixed"):
        self.mode = mode

        self.employees = {
            "sarah kim": {
                "name": "Sarah Kim",
                "role": "Engineering Manager",
                "team": "Platform",
                "email": "sarah.kim@company.example",
            },
            "aram petrosyan": {
                "name": "Aram Petrosyan",
                "role": "Backend Engineer",
                "team": "Platform",
                "email": "aram.petrosyan@company.example",
            },
            "maria lopez": {
                "name": "Maria Lopez",
                "role": "Product Manager",
                "team": "Growth",
                "email": "maria.lopez@company.example",
            },
        }

        self.teams = {
            "platform": {
                "name": "Platform",
                "manager": "Sarah Kim",
                "members": ["Sarah Kim", "Aram Petrosyan"],
                "mission": "Owns internal developer platforms, RAG infrastructure, and agent tooling.",
            },
            "growth": {
                "name": "Growth",
                "manager": "Maria Lopez",
                "members": ["Maria Lopez"],
                "mission": "Owns acquisition experiments, onboarding, and activation.",
            },
        }

        self.docs = {
            "rag checklist": (
                "Internal RAG checklist: answers must be grounded in retrieved context, "
                "include citations when sources are available, avoid unsupported claims, "
                "and say 'I don't have information about that.' when context is insufficient."
            ),
            "mail automation": (
                "Internal mail automation notes: incoming emails should be classified, "
                "draft replies should match Hayk's style, and sending should require approval."
            ),
            "checkpoint policy": (
                "Internal checkpoint policy: customer-facing agent workflows should checkpoint "
                "before human approval, before memory writes, and before irreversible actions."
            ),
        }

        self.web_results = {
            "langgraph": (
                "Public web result: LangGraph is a framework for building stateful, multi-step "
                "LLM applications with graphs, persistence, checkpointing, and human-in-the-loop flows."
            ),
            "checkpointing": (
                "Public web result: checkpointing saves intermediate workflow state so a process "
                "can pause, resume, or recover after interruption."
            ),
            "rag": (
                "Public web result: Retrieval-Augmented Generation combines search or retrieval "
                "with language-model generation to answer using external context."
            ),
        }

        self.allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

    def get_tool_descriptions(self) -> dict:
        """
        Return tool descriptions for the selected mode.
        """

        descriptions_by_mode = {
            "fixed": {
                "search_docs": (
                    "Search ONLY internal/private company documents and private project notes. "
                    "Use this for internal docs, our docs, company policy, private notes, "
                    "internal RAG, memory, checkpoint, or mail automation policy."
                ),
                "search_web": (
                    "Search ONLY public/external web-style information. "
                    "Use this for public information, external docs, online information, "
                    "recent news, or specifically when the user says web."
                ),
                "get_employee": (
                    "Look up exactly one employee by PERSON NAME, such as Sarah Kim. "
                    "Use this for a person's email, role, or team."
                ),
                "get_team": (
                    "Look up exactly one TEAM by TEAM NAME, such as Platform or Growth. "
                    "Use this for team manager, team members, or team mission."
                ),
                "calculator": (
                    "Calculate math expressions and numeric questions. "
                    "Use this for arithmetic, percentages, multiplication, division, addition, or subtraction."
                ),
            }
        }

        if self.mode not in descriptions_by_mode:
            raise ValueError(f"Unknown tool mode: {self.mode}")

        return descriptions_by_mode[self.mode]

    def search_docs(self, query: str) -> str:
        """
        Search internal/private company documents.
        """

        query_lower = query.lower()
        matches = []

        for title, content in self.docs.items():
            title_tokens = set(title.split())
            query_tokens = set(query_lower.split())

            if title in query_lower or title_tokens.intersection(query_tokens):
                matches.append(f"{title}: {content}")

        if not matches:
            return "No internal document result found."

        return "\n".join(matches)

    def search_web(self, query: str) -> str:
        """
        Search mock public web results.
        """

        query_lower = query.lower()
        matches = []

        for keyword, content in self.web_results.items():
            if keyword in query_lower:
                matches.append(content)

        if not matches:
            return "No public web result found."

        return "\n".join(matches)

    def get_employee(self, name: str) -> str:
        """
        Look up an employee by person name.
        """

        key = name.strip().lower()
        employee = self.employees.get(key)

        if employee is None:
            return (
                f"No employee found for '{name}'. "
                "Use a specific person name such as Sarah Kim."
            )

        return (
            f"Name: {employee['name']}\n"
            f"Role: {employee['role']}\n"
            f"Team: {employee['team']}\n"
            f"Email: {employee['email']}"
        )

    def get_team(self, name: str) -> str:
        """
        Look up a team by team name.
        """

        key = name.strip().lower()
        team = self.teams.get(key)

        if team is None:
            return (
                f"No team found for '{name}'. "
                "Use a team name such as Platform or Growth."
            )

        members = ", ".join(team["members"])

        return (
            f"Team: {team['name']}\n"
            f"Manager: {team['manager']}\n"
            f"Members: {members}\n"
            f"Mission: {team['mission']}"
        )

    def calculator(self, expression: str) -> str:
        """
        Calculate a simple math expression.
        """

        try:
            normalized_expression = self._normalize_math_expression(expression)
            parsed = ast.parse(normalized_expression, mode="eval")
            result = self._safe_eval_math(parsed.body)

            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return str(result)

        except Exception as error:
            return f"Calculator error: {error}"

    def _normalize_math_expression(self, expression: str) -> str:
        """
        Convert common percent phrasing into arithmetic.

        Example:
        18% of 2450 -> (18 / 100) * 2450
        """

        text = expression.strip().lower()

        percent_match = re.search(
            r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)",
            text,
        )

        if percent_match:
            percent = percent_match.group(1)
            amount = percent_match.group(2)
            return f"({percent} / 100) * {amount}"

        text = text.replace("%", "/100")
        return text

    def _safe_eval_math(self, node):
        """
        Safely evaluate a simple arithmetic AST.
        """

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            left = self._safe_eval_math(node.left)
            right = self._safe_eval_math(node.right)

            operator_type = type(node.op)

            if operator_type not in self.allowed_operators:
                raise ValueError("Unsupported operator.")

            return self.allowed_operators[operator_type](left, right)

        if isinstance(node, ast.UnaryOp):
            operand = self._safe_eval_math(node.operand)
            operator_type = type(node.op)

            if operator_type not in self.allowed_operators:
                raise ValueError("Unsupported unary operator.")

            return self.allowed_operators[operator_type](operand)

        raise ValueError("Unsupported expression.")

    def get_tools(self) -> list:
        """
        Build LangChain StructuredTool objects from instance methods.
        """

        descriptions = self.get_tool_descriptions()

        return [
            StructuredTool.from_function(
                name="search_docs",
                func=self.search_docs,
                description=descriptions["search_docs"],
            ),
            StructuredTool.from_function(
                name="search_web",
                func=self.search_web,
                description=descriptions["search_web"],
            ),
            StructuredTool.from_function(
                name="get_employee",
                func=self.get_employee,
                description=descriptions["get_employee"],
            ),
            StructuredTool.from_function(
                name="get_team",
                func=self.get_team,
                description=descriptions["get_team"],
            ),
            StructuredTool.from_function(
                name="calculator",
                func=self.calculator,
                description=descriptions["calculator"],
            ),
        ]

    def get_tool_map(self) -> dict:
        """
        Return tools as dictionary by tool name.
        """

        tools = self.get_tools()

        return {
            tool.name: tool
            for tool in tools
        }

    def demo(self):
        """
        Small local test for ToolRegistry.
        """

        print("=" * 100)
        print("WEEK 5 TOOL REGISTRY DEMO")
        print("=" * 100)

        tool_map = self.get_tool_map()

        print("Available tools:")
        for tool_name in tool_map:
            print(f"- {tool_name}")

        print("-" * 100)
        print("Calculator test:")
        print(tool_map["calculator"].invoke({"expression": "18% of 2450"}))

        print("-" * 100)
        print("Team lookup test:")
        print(tool_map["get_team"].invoke({"name": "Platform"}))

        print("=" * 100)


@dataclass
class AgentRunResult:
    """
    Result object returned by ToolCallingAgent.
    """

    question: str
    answer: str
    trajectory: list[dict[str, Any]]
    messages: list[Any]


class ToolCallingAgent:
    """
    Class-based tool-calling agent.

    This class owns:
    - llm
    - tool registry
    - tools
    - tool map
    - trajectory

    This replaces the old flat run_agent / run_agent_with_history functions.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        max_steps: int = 5,
    ):
        self.registry = registry
        self.max_steps = max_steps
        self.llm = create_llm()
        self.tools = self.registry.get_tools()
        self.tool_map = self.registry.get_tool_map()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.trajectory = []

    def run(
        self,
        question: str,
        assembled_context: str = "",
        verbose: bool = True,
    ) -> AgentRunResult:
        """
        Run one agent turn.

        assembled_context is optional memory/context injected by ChatSession later.
        """

        self.reset_trajectory()

        system_prompt = self._build_system_prompt(
            assembled_context=assembled_context,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]

        if verbose:
            print("=" * 100)
            print("WEEK 5 TOOL CALLING AGENT RUN")
            print("=" * 100)
            print(f"Question: {question}")
            print("-" * 100)

        for step in range(1, self.max_steps + 1):
            ai_message = self.llm_with_tools.invoke(messages)
            messages.append(ai_message)

            tool_calls = getattr(ai_message, "tool_calls", [])

            if not tool_calls:
                answer = self._message_to_text(ai_message)

                if verbose:
                    print("Final answer:")
                    print(answer)
                    print("=" * 100)

                return AgentRunResult(
                    question=question,
                    answer=answer,
                    trajectory=self.get_trajectory(),
                    messages=messages,
                )

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]

                selected_tool = self.tool_map.get(tool_name)

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

                self.trajectory.append(trajectory_row)

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

        return AgentRunResult(
            question=question,
            answer=fallback_answer,
            trajectory=self.get_trajectory(),
            messages=messages,
        )

    def get_trajectory(self) -> list[dict[str, Any]]:
        """
        Return a copy of the current trajectory.
        """

        return list(self.trajectory)

    def reset_trajectory(self):
        """
        Clear trajectory before a new run.
        """

        self.trajectory = []

    def _build_system_prompt(self, assembled_context: str = "") -> str:
        """
        Build the system prompt for the agent.
        """

        base_prompt = """
You are a multi-tool assistant.

You must use native structured tool calls when a tool is appropriate.

Important rules:
1. Select tools based on the tool descriptions. Tool descriptions are authoritative.
2. Do not hand-parse tool names from text.
3. If the user asks for math, use the calculator tool.
4. If the user asks about internal/private docs, use search_docs.
5. If the user asks about public web information, use search_web.
6. If the user asks about a person, use get_employee.
7. If the user asks about a team, use get_team.
8. If the user uses a pronoun like "her", "him", or "that" and no prior context is available,
   say you do not have enough context.
9. Keep final answers concise.
"""

        context = assembled_context.strip()

        if not context:
            return base_prompt

        return (
            base_prompt
            + "\n\nConversation memory/context injected by the application:\n"
            + context
        )

    def _message_to_text(self, message) -> str:
        """
        Convert LangChain message content to plain text.
        """

        content = message.content

        if isinstance(content, str):
            return content.strip()

        return str(content).strip()

class ConversationMemory:
    """
    Class-based conversation memory.

    This class owns:
    - recent turns
    - rolling summary
    - max_turns configuration
    """

    def __init__(self, max_turns: int = 4):
        self.max_turns = max_turns
        self.turns = []
        self.rolling_summary = ""

    def add_turn(self, user_message: str, assistant_message: str):
        """
        Add one user/assistant turn to memory.
        """

        self.turns.append(
            {
                "user": user_message,
                "assistant": assistant_message,
            }
        )

        self._roll_if_needed()

    def context(self) -> str:
        """
        Assemble memory context that will be injected into the next agent turn.
        """

        parts = []

        if self.rolling_summary:
            parts.append("Rolling summary:")
            parts.append(self.rolling_summary)

        if self.turns:
            parts.append("Recent turns:")

            for index, turn in enumerate(self.turns, start=1):
                parts.append(f"Turn {index} user: {turn['user']}")
                parts.append(f"Turn {index} assistant: {turn['assistant']}")

        if not parts:
            return "No previous conversation context."

        return "\n".join(parts)

    def clear(self):
        """
        Clear all memory.
        """

        self.turns = []
        self.rolling_summary = ""

    def _roll_if_needed(self):
        """
        Move old turns into rolling summary when the buffer is too long.
        """

        while len(self.turns) > self.max_turns:
            old_turn = self.turns.pop(0)

            summary_line = (
                f"User asked: {old_turn['user']} "
                f"Assistant answered: {old_turn['assistant']}"
            )

            if self.rolling_summary:
                self.rolling_summary += "\n" + summary_line
            else:
                self.rolling_summary = summary_line


class ChatSession:
    """
    Class-based multi-turn chat session.

    This class owns:
    - agent
    - memory
    - transcript

    This demonstrates composition:
    ChatSession has-a ToolCallingAgent.
    ChatSession has-a ConversationMemory.
    """

    def __init__(
        self,
        agent: ToolCallingAgent,
        memory: ConversationMemory,
    ):
        self.agent = agent
        self.memory = memory
        self.transcript = []

    def ask(
        self,
        user_message: str,
        verbose: bool = True,
    ) -> dict:
        """
        Ask one message using memory.
        """

        assembled_context = self.memory.context()

        result = self.agent.run(
            question=user_message,
            assembled_context=assembled_context,
            verbose=verbose,
        )

        self.memory.add_turn(
            user_message=user_message,
            assistant_message=result.answer,
        )

        turn_log = {
            "user": user_message,
            "assembled_context": assembled_context,
            "trajectory": result.trajectory,
            "answer": result.answer,
        }

        self.transcript.append(turn_log)

        return turn_log

    def get_transcript(self) -> list[dict]:
        """
        Return the chat transcript.
        """

        return list(self.transcript)


class RoutingEvaluator:
    """
    Class-based routing evaluator.

    This class owns:
    - agent
    - golden set
    - evaluation results

    It measures whether the model selected the expected first tool.
    """

    def __init__(self, agent: ToolCallingAgent):
        self.agent = agent
        self.golden_set = [
            {
                "id": "R1",
                "question": "What is 18% of 2450?",
                "expected_tool": "calculator",
            },
            {
                "id": "R2",
                "question": "Who manages the Platform team?",
                "expected_tool": "get_team",
            },
            {
                "id": "R3",
                "question": "What is Sarah Kim's email?",
                "expected_tool": "get_employee",
            },
            {
                "id": "R4",
                "question": "According to our internal docs, what does the RAG checklist say about citations?",
                "expected_tool": "search_docs",
            },
            {
                "id": "R5",
                "question": "Search the web for public information about LangGraph checkpointing.",
                "expected_tool": "search_web",
            },
            {
                "id": "R6",
                "question": "According to our internal docs, what is our checkpoint policy?",
                "expected_tool": "search_docs",
            },
            {
                "id": "R7",
                "question": "Find public web information about RAG.",
                "expected_tool": "search_web",
            },
            {
                "id": "R8",
                "question": "What does the internal team directory say about the Platform team?",
                "expected_tool": "get_team",
            },
        ]
        self.results = []

    def evaluate(self, verbose: bool = True) -> dict:
        """
        Evaluate routing accuracy over the golden set.
        """

        self.results = []

        for item in self.golden_set:
            actual = self._get_first_tool_call(
                question=item["question"],
            )

            expected_tool = item["expected_tool"]
            actual_tool = actual["actual_tool"]

            result = {
                "id": item["id"],
                "question": item["question"],
                "expected_tool": expected_tool,
                "actual_tool": actual_tool,
                "tool_args": actual["tool_args"],
                "passed": actual_tool == expected_tool,
            }

            self.results.append(result)

        passed = sum(
            1
            for result in self.results
            if result["passed"]
        )

        total = len(self.results)
        accuracy = passed / total if total else 0

        report = {
            "passed": passed,
            "total": total,
            "accuracy": accuracy,
            "results": self.get_results(),
        }

        if verbose:
            self.print_report(report)

        return report

    def get_results(self) -> list[dict]:
        """
        Return a copy of evaluation results.
        """

        return list(self.results)

    def print_report(self, report: dict):
        """
        Print routing evaluation report.
        """

        print("\n")
        print("=" * 100)
        print("WEEK 5 ROUTING EVALUATION")
        print("=" * 100)

        for result in report["results"]:
            print("-" * 100)
            print(f"ID: {result['id']}")
            print(f"Question: {result['question']}")
            print(f"Expected tool: {result['expected_tool']}")
            print(f"Actual tool: {result['actual_tool']}")
            print(f"Tool args: {result['tool_args']}")
            print(f"Pass: {result['passed']}")

        print("=" * 100)
        print(
            f"Routing accuracy: {report['passed']}/{report['total']} "
            f"= {report['accuracy']:.2f}"
        )
        print("=" * 100)

    def _get_first_tool_call(self, question: str) -> dict:
        """
        Ask the LLM to select exactly one tool and return the first structured tool call.
        """

        messages = [
            SystemMessage(
                content=(
                    "You are a tool-routing evaluator. "
                    "Select exactly one tool for the user's request. "
                    "Use the tool descriptions as the source of truth. "
                    "Do not answer directly. "
                    "Call exactly one tool."
                )
            ),
            HumanMessage(content=question),
        ]

        ai_message = self.agent.llm_with_tools.invoke(messages)
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

if __name__ == "__main__":
    registry = ToolRegistry(mode="fixed")

    print("\n")
    registry.demo()

    print("\n")
    agent = ToolCallingAgent(
        registry=registry,
        max_steps=5,
    )

    result = agent.run(
        "What is 18% of 2450?",
        verbose=True,
    )

    print("\nTrajectory proof:")
    for row in result.trajectory:
        compact_row = {
            "tool": row["tool"],
            "args": row["args"],
        }
        print(compact_row)

    print("\nFinal answer:")
    print(result.answer)

    print("\n")
    print("=" * 100)
    print("WEEK 5 MEMORY CHAT DEMO")
    print("=" * 100)

    memory = ConversationMemory(max_turns=4)

    chat = ChatSession(
        agent=agent,
        memory=memory,
    )

    first_turn = chat.ask(
        "Who manages the Platform team?",
        verbose=True,
    )

    print("\nAssembled context before second turn:")
    print("-" * 100)
    print(memory.context())
    print("-" * 100)

    second_turn = chat.ask(
        "And her email?",
        verbose=True,
    )

    print("\nMemory demo result:")
    print("-" * 100)
    print("First answer:")
    print(first_turn["answer"])
    print()
    print("Second answer:")
    print(second_turn["answer"])
    print("=" * 100)
    evaluator = RoutingEvaluator(agent=agent)
    evaluator.evaluate(verbose=True)