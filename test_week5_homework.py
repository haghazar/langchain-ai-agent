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


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(
            f"{message}\nExpected: {expected}\nActual: {actual}"
        )


def assert_contains(text, expected_substring, message):
    if expected_substring not in text:
        raise AssertionError(
            f"{message}\nExpected substring: {expected_substring}\nActual text: {text}"
        )


def test_structured_tool_calling():
    print("\n" + "=" * 100)
    print("TEST 1: STRUCTURED TOOL CALLING")
    print("=" * 100)

    registry = ToolRegistry(mode="fixed")
    agent = ToolCallingAgent(registry=registry)

    result = agent.run(
        "What is 18% of 2450?",
        verbose=False,
    )

    first_tool = result.trajectory[0]["tool"]
    answer = result.answer

    assert_equal(
        first_tool,
        "calculator",
        "The agent should select calculator through structured tool calling.",
    )

    assert_contains(
        answer,
        "441",
        "The calculator result should be 441.",
    )

    print("TEST 1 PASSED")


def test_class_based_memory_followup():
    print("\n" + "=" * 100)
    print("TEST 2: CLASS-BASED MEMORY FOLLOW-UP")
    print("=" * 100)

    registry = ToolRegistry(mode="fixed")
    agent = ToolCallingAgent(registry=registry)
    memory = ConversationMemory(max_turns=4)

    chat = ChatSession(
        agent=agent,
        memory=memory,
    )

    chat.ask(
        "Who manages the Platform team?",
        verbose=False,
    )

    context_before_second_turn = memory.context()

    second_turn = chat.ask(
        "And her email?",
        verbose=False,
    )

    assert_contains(
        context_before_second_turn,
        "Sarah Kim",
        "Memory context should contain Sarah Kim before the follow-up question.",
    )

    assert_contains(
        second_turn["answer"],
        "sarah.kim@company.example",
        "The follow-up should resolve 'her' to Sarah Kim using memory.",
    )

    print("TEST 2 PASSED")


def test_routing_evaluator():
    print("\n" + "=" * 100)
    print("TEST 3: ROUTING EVALUATOR")
    print("=" * 100)

    registry = ToolRegistry(mode="fixed")
    agent = ToolCallingAgent(registry=registry)
    evaluator = RoutingEvaluator(agent=agent)

    report = evaluator.evaluate(verbose=False)

    assert_equal(
        report["passed"],
        report["total"],
        "All routing examples should pass in fixed mode.",
    )

    print(
        f"Routing accuracy: {report['passed']}/{report['total']} "
        f"= {report['accuracy']:.2f}"
    )

    print("TEST 3 PASSED")


def test_semantic_memory():
    print("\n" + "=" * 100)
    print("TEST 4: SEMANTIC MEMORY")
    print("=" * 100)

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

    recalled_facts = assistant.recall_style_without_email()

    assert_equal(
        len(recalled_facts),
        1,
        "Semantic memory should recall one stored style fact.",
    )

    assert_contains(
        recalled_facts[0],
        "concise, warm, professional",
        "Semantic memory should recall Hayk's email style preference.",
    )

    print("TEST 4 PASSED")


def test_episodic_memory_flips_decision():
    print("\n" + "=" * 100)
    print("TEST 5: EPISODIC MEMORY FLIPS TRIAGE DECISION")
    print("=" * 100)

    memory_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=True,
    )

    assistant = EmailAssistant(
        memory_store=memory_store,
        triage_router=EmailTriageRouter(memory_store),
        response_agent=EmailResponseAgent(memory_store),
    )

    email = EmailMessage(
        sender="important.client@example.com",
        subject="Checking updates",
        body="Just checking if there are any updates on this.",
    )

    before = assistant.process_email(email)

    assert_equal(
        before["decision"].action,
        "archive",
        "Before episodic memory, the email should be archived.",
    )

    assistant.learn_from_example(
        email_text="Just checking if there are any updates.",
        decision="reply",
        reason="A follow-up from an important client should receive an acknowledgment.",
    )

    after = assistant.process_email(email)

    assert_equal(
        after["decision"].action,
        "reply",
        "After one episodic example, the same email should require a reply.",
    )

    assert_equal(
        after["decision"].memory_used,
        "episodic",
        "The changed decision should be caused by episodic memory.",
    )

    print("TEST 5 PASSED")


def test_procedural_memory_persistence():
    print("\n" + "=" * 100)
    print("TEST 6: PROCEDURAL MEMORY PERSISTENCE")
    print("=" * 100)

    memory_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=True,
    )

    assistant = EmailAssistant(
        memory_store=memory_store,
        triage_router=EmailTriageRouter(memory_store),
        response_agent=EmailResponseAgent(memory_store),
    )

    assistant.apply_feedback(
        "Use a formal banking tone and avoid casual phrases."
    )

    reloaded_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=False,
    )

    instructions = reloaded_store.get_procedural_instructions()
    instructions_text = "\n".join(instructions)

    assert_contains(
        instructions_text,
        "formal banking tone",
        "Procedural memory should persist after reloading JSON store.",
    )

    assert_contains(
        instructions_text,
        "Never send emails automatically.",
        "Safety instruction should remain after procedural rewrite.",
    )

    print("TEST 6 PASSED")


def main():
    test_structured_tool_calling()
    test_class_based_memory_followup()
    test_routing_evaluator()
    test_semantic_memory()
    test_episodic_memory_flips_decision()
    test_procedural_memory_persistence()

    print("\n" + "=" * 100)
    print("ALL WEEK 5 CORE TESTS PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()
    