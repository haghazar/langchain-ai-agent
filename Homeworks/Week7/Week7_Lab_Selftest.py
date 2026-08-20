"""
Selftest for Week 7.

This file tests the plain Python parts first:
- assign_workers
- route_after_review

It does not call the LLM.
"""

from langgraph.types import Send

from Week7_Lab_Pipeline_Skeleton import (
    MAX_REVISIONS,
    assign_workers,
    route_after_review,
)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(
            f"{label} failed. Expected {expected!r}, got {actual!r}"
        )


def test_assign_workers() -> None:
    state = {
        "question": "Should we use one accounting integration service or several?",
        "sub_questions": [
            "What are the benefits of one integration service?",
            "What are the risks of several integration services?",
            "What should a small team prioritize?",
        ],
        "findings": [],
        "draft": "",
        "feedback": "",
        "revision_count": 0,
        "approved": False,
    }

    sends = assign_workers(state)

    assert_equal(len(sends), 3, "assign_workers count")

    for index, send in enumerate(sends):
        if not isinstance(send, Send):
            raise AssertionError(
                f"assign_workers item {index} is not a Send object: {send!r}"
            )

        assert_equal(send.node, "worker", f"assign_workers node {index}")

    assert_equal(
        sends[0].arg,
        {
            "sub_question": "What are the benefits of one integration service?",
        },
        "assign_workers first payload",
    )

    assert_equal(
        sends[1].arg,
        {
            "sub_question": "What are the risks of several integration services?",
        },
        "assign_workers second payload",
    )

    assert_equal(
        sends[2].arg,
        {
            "sub_question": "What should a small team prioritize?",
        },
        "assign_workers third payload",
    )

    print("TEST 1 PASSED: assign_workers creates one Send per sub-question")


def test_route_after_review() -> None:
    approved_state = {
        "approved": True,
        "revision_count": 0,
    }

    rejected_first_time = {
        "approved": False,
        "revision_count": 0,
    }

    rejected_at_limit = {
        "approved": False,
        "revision_count": MAX_REVISIONS,
    }

    rejected_over_limit = {
        "approved": False,
        "revision_count": MAX_REVISIONS + 1,
    }

    assert_equal(
        route_after_review(approved_state),
        "end",
        "approved route",
    )

    assert_equal(
        route_after_review(rejected_first_time),
        "revise",
        "first rejection route",
    )

    assert_equal(
        route_after_review(rejected_at_limit),
        "end",
        "max revision route",
    )

    assert_equal(
        route_after_review(rejected_over_limit),
        "end",
        "over max revision route",
    )

    print("TEST 2 PASSED: route_after_review routes correctly")


def main() -> None:
    print("=" * 100)
    print("WEEK 7 SELFTEST")
    print("=" * 100)

    test_assign_workers()
    test_route_after_review()

    print("=" * 100)
    print("ALL WEEK 7 SELFTESTS PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()