from eval_answers import (
    create_judge_chain,
    parse_judge_json,
    normalize_score,
    score_to_pass,
)
from eval_set import GOLDEN_QUERIES
from rag import create_retriever, format_documents


def get_query_item(query_id):
    """
    Find one query item by ID from the golden query set.
    """

    for item in GOLDEN_QUERIES:
        if item["id"] == query_id:
            return item

    raise ValueError(f"Query ID not found: {query_id}")


def get_context_for_question(question):
    """
    Retrieve context for one question using the same retriever as the RAG system.
    """

    retriever = create_retriever()
    retrieved_documents = retriever.invoke(question)
    context = format_documents(retrieved_documents)

    return context


def judge_manual_answer(judge_chain, question, reference, context, answer):
    """
    Run the judge on a manually provided answer.
    """

    raw_output = judge_chain.invoke(
        {
            "question": question,
            "reference": reference,
            "context": context,
            "answer": answer,
        }
    )

    result = parse_judge_json(raw_output)

    faithfulness_score = normalize_score(
        result.get("faithfulness_score")
    )
    correctness_score = normalize_score(
        result.get("correctness_score")
    )

    return {
        "answer": answer,
        "faithfulness_reason": result.get("faithfulness_reason", ""),
        "faithfulness_score": faithfulness_score,
        "faithfulness_pass": score_to_pass(faithfulness_score),
        "correctness_reason": result.get("correctness_reason", ""),
        "correctness_score": correctness_score,
        "correctness_pass": score_to_pass(correctness_score),
    }


def print_result(label, result):
    """
    Print one stress-test result.
    """

    print("=" * 100)
    print(label)
    print("-" * 100)
    print("Answer:")
    print(result["answer"])
    print()

    print("Faithfulness:")
    print(f"Reason: {result['faithfulness_reason']}")
    print(f"Score: {result['faithfulness_score']}")
    print(f"Pass: {result['faithfulness_pass']}")
    print()

    print("Correctness:")
    print(f"Reason: {result['correctness_reason']}")
    print(f"Score: {result['correctness_score']}")
    print(f"Pass: {result['correctness_pass']}")
    print("=" * 100)
    print()


def main():
    """
    Stress-test the judge for verbosity bias.

    We compare:
    1. a concise correct answer;
    2. a verbose but still correct answer.
    """

    item = get_query_item("Q2A")

    question = item["query"]
    reference = item["reference"]
    context = get_context_for_question(question)

    concise_answer = (
        "A peer from the owner’s organization and a regulator’s organization "
        "must endorse any transfer requests."
    )

    verbose_answer = (
        "A transfer request must be endorsed by a peer from the owner’s "
        "organization and by a regulator’s organization. In other words, "
        "both the owner’s side and the regulator’s side need to sign off "
        "before the asset can be transferred. This is the required approval "
        "path for the transfer request."
    )

    judge_chain = create_judge_chain()

    concise_result = judge_manual_answer(
        judge_chain=judge_chain,
        question=question,
        reference=reference,
        context=context,
        answer=concise_answer,
    )

    verbose_result = judge_manual_answer(
        judge_chain=judge_chain,
        question=question,
        reference=reference,
        context=context,
        answer=verbose_answer,
    )

    print("#" * 100)
    print("Verbosity Bias Stress Test")
    print("#" * 100)
    print(f"Question ID: {item['id']}")
    print(f"Question: {question}")
    print()

    print_result("Concise Answer", concise_result)
    print_result("Verbose Answer", verbose_result)

    print("#" * 100)
    print("Side-by-side Summary")
    print("#" * 100)
    print(
        "| Answer Type | Faithfulness Score | Correctness Score |"
    )
    print(
        "|-------------|--------------------|-------------------|"
    )
    print(
        f"| Concise | {concise_result['faithfulness_score']} | "
        f"{concise_result['correctness_score']} |"
    )
    print(
        f"| Verbose | {verbose_result['faithfulness_score']} | "
        f"{verbose_result['correctness_score']} |"
    )
    print()

    verbose_total = (
        verbose_result["faithfulness_score"]
        + verbose_result["correctness_score"]
    )

    concise_total = (
        concise_result["faithfulness_score"]
        + concise_result["correctness_score"]
    )

    if verbose_total > concise_total:
        print("Result: Verbosity bias appeared.")
    else:
        print("Result: No verbosity bias appeared.")


if __name__ == "__main__":
    main()