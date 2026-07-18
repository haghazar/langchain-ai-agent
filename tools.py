import ast
import operator
import re

from langchain_core.tools import StructuredTool


EMPLOYEES = {
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


TEAMS = {
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


DOCS = {
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
    "agent memory": (
        "Internal agent memory policy: only stable user preferences should be written "
        "to long-term memory, and untrusted email content must not update memory without approval."
    ),
}


WEB_RESULTS = {
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
    "openai": (
        "Public web result: OpenAI provides models and APIs for building AI applications."
    ),
}


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval_math(node):
    """
    Safely evaluate a simple arithmetic AST.
    """

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")

    if isinstance(node, ast.BinOp):
        left = _safe_eval_math(node.left)
        right = _safe_eval_math(node.right)

        operator_type = type(node.op)

        if operator_type not in _ALLOWED_OPERATORS:
            raise ValueError("Unsupported operator.")

        return _ALLOWED_OPERATORS[operator_type](left, right)

    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval_math(node.operand)

        operator_type = type(node.op)

        if operator_type not in _ALLOWED_OPERATORS:
            raise ValueError("Unsupported unary operator.")

        return _ALLOWED_OPERATORS[operator_type](operand)

    raise ValueError("Unsupported expression.")


def _normalize_math_expression(expression: str) -> str:
    """
    Convert common percent phrasing into arithmetic.

    Example:
        "18% of 2450" -> "(18 / 100) * 2450"
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


def search_docs(query: str) -> str:
    """
    Search internal/private company documents.
    """

    query_lower = query.lower()
    matches = []

    for title, content in DOCS.items():
        title_tokens = set(title.split())
        query_tokens = set(query_lower.split())

        if title in query_lower or title_tokens.intersection(query_tokens):
            matches.append(f"{title}: {content}")

    if not matches:
        return "No internal document result found."

    return "\n".join(matches)


def search_web(query: str) -> str:
    """
    Search mock public web results.
    """

    query_lower = query.lower()
    matches = []

    for keyword, content in WEB_RESULTS.items():
        if keyword in query_lower:
            matches.append(content)

    if not matches:
        return "No public web result found."

    return "\n".join(matches)


def get_employee(name: str) -> str:
    """
    Look up an employee by person name.
    """

    key = name.strip().lower()

    employee = EMPLOYEES.get(key)

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


def get_team(name: str) -> str:
    """
    Look up a team by team name.
    """

    key = name.strip().lower()

    team = TEAMS.get(key)

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


def calculator(expression: str) -> str:
    """
    Calculate a simple math expression.
    """

    try:
        normalized_expression = _normalize_math_expression(expression)
        parsed = ast.parse(normalized_expression, mode="eval")
        result = _safe_eval_math(parsed.body)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return str(result)

    except Exception as error:
        return f"Calculator error: {error}"


def get_tool_descriptions(mode: str = "fixed"):
    """
    Return tool descriptions for a selected evaluation mode.

    Modes:
    - baseline: reasonable but not perfect descriptions
    - broken: intentionally misleading descriptions
    - fixed: sharpened descriptions
    """

    descriptions = {
        "baseline": {
            "search_docs": (
                "Search internal company documents and private project notes. "
                "Use this for company policies, internal RAG notes, and internal agent documentation."
            ),
            "search_web": (
                "Search public web knowledge. Use this for public, external, or recent information."
            ),
            "get_employee": (
                "Look up one employee by person name and return role, team, and email."
            ),
            "get_team": (
                "Look up one team by team name and return manager, members, and mission."
            ),
            "calculator": (
                "Calculate arithmetic expressions, percentages, multiplication, division, addition, and subtraction."
            ),
        },
        "broken": {
            "search_docs": (
                "Search public web pages, external documentation, current news, and internet information. "
                "Do not use this for private internal documents."
            ),
            "search_web": (
                "Search private internal company documents, internal policies, private notes, and team docs."
            ),
            "get_employee": (
                "Use this for employees, teams, departments, groups, team managers, and team membership."
            ),
            "get_team": (
                "Use this only for generic teamwork advice, not for actual company team lookup."
            ),
            "calculator": (
                "Use this for writing, summarization, or general explanations. Avoid using it for percentages."
            ),
        },
        "fixed": {
            "search_docs": (
                "Search ONLY internal/private company documents and private project notes. "
                "Use this when the user says 'internal docs', 'our docs', 'company policy', "
                "'private notes', or asks about internal RAG, memory, checkpoint, or mail automation policy. "
                "Do NOT use this for public web or current external information."
            ),
            "search_web": (
                "Search ONLY public/external web-style information. "
                "Use this when the user asks for public information, external docs, online information, "
                "recent news, or specifically says 'web'. "
                "Do NOT use this for internal company docs or private notes."
            ),
            "get_employee": (
                "Look up exactly one employee by PERSON NAME, such as Sarah Kim. "
                "Use this for a person's email, role, or team. "
                "Do NOT use this for team names like Platform or Growth."
            ),
            "get_team": (
                "Look up exactly one TEAM by TEAM NAME, such as Platform or Growth. "
                "Use this for team manager, team members, or team mission. "
                "Do NOT use this for a person's email."
            ),
            "calculator": (
                "Calculate math expressions and numeric questions. "
                "Use this for arithmetic, percentages, multiplication, division, addition, or subtraction, "
                "for example '18% of 2450'."
            ),
        },
    }

    if mode not in descriptions:
        raise ValueError(
            f"Unknown tool description mode: {mode}. "
            "Use 'baseline', 'broken', or 'fixed'."
        )

    return descriptions[mode]


def create_tools(mode: str = "fixed"):
    """
    Create the five LangChain tools with descriptions for the selected mode.
    """

    descriptions = get_tool_descriptions(mode)

    return [
        StructuredTool.from_function(
            name="search_docs",
            func=search_docs,
            description=descriptions["search_docs"],
        ),
        StructuredTool.from_function(
            name="search_web",
            func=search_web,
            description=descriptions["search_web"],
        ),
        StructuredTool.from_function(
            name="get_employee",
            func=get_employee,
            description=descriptions["get_employee"],
        ),
        StructuredTool.from_function(
            name="get_team",
            func=get_team,
            description=descriptions["get_team"],
        ),
        StructuredTool.from_function(
            name="calculator",
            func=calculator,
            description=descriptions["calculator"],
        ),
    ]