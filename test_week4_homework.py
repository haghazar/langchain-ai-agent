from graph_agent import ask_graph, resume_graph, show_thread_state


def assert_equal(actual, expected, message):
    """
    Simple assertion helper with readable output.
    """

    if actual != expected:
        raise AssertionError(
            f"{message}\nExpected: {expected}\nActual: {actual}"
        )


def assert_contains(text, expected_substring, message):
    """
    Check that expected_substring exists inside text.
    """

    if expected_substring not in text:
        raise AssertionError(
            f"{message}\nExpected substring: {expected_substring}\nActual text: {text}"
        )


def test_thread_memory():
    """
    Test 1:
    The graph should remember previous messages inside the same thread_id.

    Expected:
    - First question goes to retrieve.
    - Second question asks about conversation history.
    - Graph should answer directly from thread memory.
    """

    print("\n" + "#" * 100)
    print("TEST 1: THREAD MEMORY")
    print("#" * 100)

    thread_id = "test-thread-memory"

    ask_graph(
        "What does the chaincode verify before transferring the asset?",
        thread_id=thread_id,
    )

    resume_graph(
        thread_id=thread_id,
        approved=True,
    )

    ask_graph(
        "What was my previous question?",
        thread_id=thread_id,
    )

    final_result = resume_graph(
        thread_id=thread_id,
        approved=True,
    )

    state = show_thread_state(thread_id)
    values = state.values

    assert_equal(
        values["route"],
        "answer_directly",
        "The second question should be answered directly from thread memory.",
    )

    assert_contains(
        values["answer"],
        "What does the chaincode verify before transferring the asset?",
        "The graph should remember the previous user question.",
    )

    assert_equal(
        values["approved"],
        True,
        "The final answer should be approved.",
    )

    print("TEST 1 PASSED: Thread memory works.")


def test_reject_revise_approve():
    """
    Test 2:
    The graph should pause for human approval.
    If rejected, it should revise the answer and ask for approval again.

    Expected:
    - First draft pauses for approval.
    - Human rejects with feedback.
    - Graph revises answer.
    - Graph pauses again.
    - Human approves.
    - Final answer is saved.
    """

    print("\n" + "#" * 100)
    print("TEST 2: REJECT → REVISE → APPROVE")
    print("#" * 100)

    thread_id = "test-reject-revise-approve"

    first_result = ask_graph(
        "Which organizations must endorse any transfer requests?",
        thread_id=thread_id,
    )

    if "__interrupt__" not in first_result:
        raise AssertionError("The graph should pause for first human approval.")

    second_result = resume_graph(
        thread_id=thread_id,
        approved=False,
        feedback="Make the answer shorter and mention only the organizations.",
    )

    if "__interrupt__" not in second_result:
        raise AssertionError(
            "After rejection, the graph should revise and pause for approval again."
        )

    final_result = resume_graph(
        thread_id=thread_id,
        approved=True,
    )

    state = show_thread_state(thread_id)
    values = state.values

    assert_equal(
        values["approved"],
        True,
        "The revised answer should be approved.",
    )

    assert_contains(
        values["answer"],
        "owner",
        "The final answer should mention the owner organization.",
    )

    assert_contains(
        values["answer"],
        "regulator",
        "The final answer should mention the regulator organization.",
    )

    print("TEST 2 PASSED: Reject, revise, and approve flow works.")


def test_out_of_domain_guard():
    """
    Test 3:
    The graph should not answer from outside knowledge.

    Expected:
    - The graph may try retrieval.
    - If context is insufficient, it should not hallucinate.
    - Final answer should be:
      I don't have information about that.
    """

    print("\n" + "#" * 100)
    print("TEST 3: OUT-OF-DOMAIN GUARD")
    print("#" * 100)

    thread_id = "test-out-of-domain-guard"

    first_result = ask_graph(
        "When was the Eiffel Tower built?",
        thread_id=thread_id,
        max_retries=1,
    )

    if "__interrupt__" not in first_result:
        raise AssertionError("The graph should pause for human approval.")

    final_result = resume_graph(
        thread_id=thread_id,
        approved=True,
    )

    state = show_thread_state(thread_id)
    values = state.values

    assert_equal(
        values["answer"],
        "I don't have information about that.",
        "The graph should not answer out-of-domain questions from outside knowledge.",
    )

    print("TEST 3 PASSED: Out-of-domain hallucination guard works.")


def main():
    """
    Run all Week 4 homework tests.
    """

    test_thread_memory()
    test_reject_revise_approve()
    test_out_of_domain_guard()

    print("\n" + "=" * 100)
    print("ALL WEEK 4 TESTS PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()