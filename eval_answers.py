import json
from json import JSONDecodeError

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import Config
from eval_set import get_in_domain_queries
from rag import answer_question, create_retriever, create_answer_chain


PASS_THRESHOLD = 4


def create_judge_llm():
    """
    Create the LLM judge.

    The judge runs at temperature 0 because evaluation should be as stable
    and deterministic as possible.
    """

    Config()

    judge_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    return judge_llm


def create_judge_prompt():
    """
    Create the judge prompt.

    The judge must:
    - reason before giving each score;
    - score faithfulness from 1 to 5;
    - score correctness from 1 to 5;
    - return only valid JSON.
    """

    prompt = ChatPromptTemplate.from_template(
        """
You are an evaluation judge for a RAG system.

Your task is to evaluate the RAG answer using the question, reference answer,
and retrieved context.

You must score two dimensions from 1 to 5:

1. Faithfulness:
Does every claim in the RAG answer come from and stay supported by the retrieved context?
- 5 = fully supported by the context, no unsupported claims
- 4 = mostly supported, only minor harmless wording differences
- 3 = partially supported, some claims are unclear or weakly supported
- 2 = mostly unsupported or contains important unsupported claims
- 1 = not supported by the context or contradicts the context

2. Correctness:
Does the RAG answer match the reference answer in meaning?
- 5 = fully correct and complete
- 4 = mostly correct, minor missing detail
- 3 = partially correct, important detail missing
- 2 = mostly incorrect
- 1 = incorrect or does not answer the question

Important rules:
- First provide reasoning for faithfulness, then the faithfulness score.
- Then provide reasoning for correctness, then the correctness score.
- Be strict about unsupported extra claims.
- Do not reward verbosity.
- A concise correct answer should not receive a lower score just because it is short.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not wrap the JSON in triple backticks.

Question:
{question}

Reference answer:
{reference}

Retrieved context:
{context}

RAG answer:
{answer}

Return JSON in exactly this format:
{{
  "faithfulness_reason": "reasoning before the faithfulness score",
  "faithfulness_score": 1,
  "correctness_reason": "reasoning before the correctness score",
  "correctness_score": 1
}}
"""
    )

    return prompt


def create_judge_chain():
    """
    Create the LLM judge chain.

    Input:
        question
        reference
        context
        answer

    Output:
        JSON string
    """

    prompt = create_judge_prompt()
    judge_llm = create_judge_llm()

    chain = prompt | judge_llm | StrOutputParser()

    return chain


def parse_judge_json(raw_output):
    """
    Parse the judge output as JSON.

    If parsing fails, return a safe failed evaluation.
    """

    try:
        return json.loads(raw_output)
    except JSONDecodeError:
        return {
            "faithfulness_reason": (
                "Judge output was not valid JSON, so this item is marked as failed."
            ),
            "faithfulness_score": 1,
            "correctness_reason": (
                "Judge output was not valid JSON, so this item is marked as failed."
            ),
            "correctness_score": 1,
            "raw_output": raw_output,
        }


def normalize_score(value):
    """
    Convert a judge score to an integer from 1 to 5.

    If the value is invalid, return 1.
    """

    try:
        score = int(value)
    except (TypeError, ValueError):
        return 1

    if score < 1:
        return 1

    if score > 5:
        return 5

    return score


def score_to_pass(score):
    """
    Convert a 1-5 score into pass/fail.

    Scores 4 and 5 are considered pass.
    Scores 1, 2, and 3 are considered fail.
    """

    return score >= PASS_THRESHOLD


def evaluate_one_item(item, retriever, answer_chain, judge_chain):
    """
    Run RAG and judge evaluation for one golden query.
    """

    query_id = item["id"]
    question = item["query"]
    reference = item["reference"]

    answer, context = answer_question(
        question=question,
        retriever=retriever,
        answer_chain=answer_chain
    )

    raw_judge_output = judge_chain.invoke(
        {
            "question": question,
            "reference": reference,
            "context": context,
            "answer": answer,
        }
    )

    judge_result = parse_judge_json(raw_judge_output)

    faithfulness_score = normalize_score(
        judge_result.get("faithfulness_score")
    )
    correctness_score = normalize_score(
        judge_result.get("correctness_score")
    )

    faithfulness_pass = score_to_pass(faithfulness_score)
    correctness_pass = score_to_pass(correctness_score)

    return {
        "id": query_id,
        "question": question,
        "reference": reference,
        "answer": answer,
        "context": context,
        "faithfulness_reason": judge_result.get("faithfulness_reason", ""),
        "faithfulness_score": faithfulness_score,
        "faithfulness_pass": faithfulness_pass,
        "correctness_reason": judge_result.get("correctness_reason", ""),
        "correctness_score": correctness_score,
        "correctness_pass": correctness_pass,
        "raw_judge_output": raw_judge_output,
    }


def print_item_result(result):
    """
    Print one evaluated query result.
    """

    print("=" * 100)
    print(f"ID: {result['id']}")
    print(f"Question: {result['question']}")
    print("-" * 100)

    print("RAG answer:")
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


def print_summary(results):
    """
    Print aggregate faithfulness and correctness pass-rates.
    """

    total = len(results)

    faithfulness_pass_count = sum(
        1
        for result in results
        if result["faithfulness_pass"]
    )

    correctness_pass_count = sum(
        1
        for result in results
        if result["correctness_pass"]
    )

    faithfulness_pass_rate = faithfulness_pass_count / total if total else 0
    correctness_pass_rate = correctness_pass_count / total if total else 0

    print("#" * 100)
    print("Aggregate Results")
    print("#" * 100)
    print(f"Total in-domain queries: {total}")
    print(
        f"Faithfulness pass-rate: "
        f"{faithfulness_pass_count}/{total} = {faithfulness_pass_rate:.2f}"
    )
    print(
        f"Correctness pass-rate: "
        f"{correctness_pass_count}/{total} = {correctness_pass_rate:.2f}"
    )
    print("#" * 100)


def main():
    """
    Evaluate RAG answer quality over all in-domain golden queries.
    """

    items = get_in_domain_queries()

    retriever = create_retriever()
    answer_chain = create_answer_chain()
    judge_chain = create_judge_chain()

    results = []

    for item in items:
        result = evaluate_one_item(
            item=item,
            retriever=retriever,
            answer_chain=answer_chain,
            judge_chain=judge_chain
        )

        results.append(result)
        print_item_result(result)

    print_summary(results)


if __name__ == "__main__":
    main()