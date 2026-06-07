from pathlib import Path
import argparse

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import Config


COLLECTION_NAME = "hayk_ai_agent"
DEFAULT_STORE_DIR = Path("chromadb_store")
DEFAULT_K = 4


FROZEN_QUERIES = [
    {
        "id": "Q1A",
        "query": "How is an asset tracked in public chaincode state?",
        "expected_terms": ["uuid", "public chaincode state", "ownership"],
    },
    {
        "id": "Q1B",
        "query": "What is publicly visible about the asset if its sensitive details are hidden?",
        "expected_terms": ["ownership", "public", "asset"],
    },
    {
        "id": "Q2A",
        "query": "Which organizations must endorse any transfer requests?",
        "expected_terms": ["owner", "organization", "regulator", "endorse"],
    },
    {
        "id": "Q2B",
        "query": "Whose sign-off is required before the owner can hand the asset to someone else?",
        "expected_terms": ["owner", "regulator", "endorse"],
    },
    {
        "id": "Q3A",
        "query": "How does the seller provide proof of ownership to the buyer?",
        "expected_terms": ["seller", "proof", "ownership", "buyer"],
    },
    {
        "id": "Q3B",
        "query": "How can the buyer avoid simply trusting the seller’s word?",
        "expected_terms": ["seller", "buyer", "private details"],
    },
    {
        "id": "Q4A",
        "query": "Where does the buyer record their bid details?",
        "expected_terms": ["buyer", "bid details", "private data collection"],
    },
    {
        "id": "Q4B",
        "query": "Where is the buyer’s purchase proposal kept away from other channel members?",
        "expected_terms": ["buyer", "private data collection"],
    },
    {
        "id": "Q5A",
        "query": "What does the chaincode verify before transferring the asset?",
        "expected_terms": ["chaincode", "verifies", "submitting client", "owner"],
    },
    {
    "id": "Q5B",
    "query": "What validation happens before the asset leaves the seller’s side?",
    "expected_terms": [
        "submitting client",
        "private details against the hash",
        "bid details against the hash",
    ],
},
]


def normalize_text(text: str) -> str:
    """
    Normalize text for simple keyword-based hit checking.
    """

    return (
        text.lower()
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def create_vector_store(store_dir: Path):
    """
    Load an existing ChromaDB vector store.
    """

    if not store_dir.exists():
        raise FileNotFoundError(
            f"{store_dir} was not found. Run python ingest.py first."
        )

    Config()

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview"
    )

    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(store_dir),
        embedding_function=embeddings,
    )


def is_hit(results, expected_terms: list[str]) -> bool:
    """
    Check whether the expected answer appears in the retrieved top-k chunks.

    This is a helper check.
    You should still visually inspect the printed chunks.
    """

    combined_text = "\n".join(
        document.page_content for document, _score in results
    )

    normalized = normalize_text(combined_text)

    return all(
        normalize_text(term) in normalized
        for term in expected_terms
    )


def print_retrieval_results(query_id: str, query: str, results, expected_terms: list[str]):
    """
    Print top-k retrieved chunks with distances.
    """

    top_1_distance = results[0][1] if results else None
    hit = is_hit(results, expected_terms) if results else False

    print("=" * 100)
    print(f"{query_id}: {query}")
    print("-" * 100)
    print(f"Top-1 distance: {top_1_distance}")
    print(f"Auto HIT/MISS check: {'HIT' if hit else 'MISS'}")
    print(f"Expected terms: {expected_terms}")
    print("-" * 100)

    for index, (document, score) in enumerate(results, start=1):
        source = document.metadata.get("source", "unknown source")
        page = document.metadata.get("page", None)

        print(f"Rank: {index}")
        print(f"Distance: {score}")
        print(f"Source: {source}")

        if page is not None:
            print(f"Page: {page}")

        snippet = document.page_content.replace("\n", " ")
        print(f"Chunk preview: {snippet[:500]}")
        print("-" * 100)

    return {
        "query_id": query_id,
        "query": query,
        "top_1_distance": top_1_distance,
        "hit": hit,
    }


def run_all_queries(store_dir: Path, k: int):
    """
    Run all frozen queries against the selected ChromaDB store.
    """

    vector_store = create_vector_store(store_dir)

    summary_rows = []

    for item in FROZEN_QUERIES:
        results = vector_store.similarity_search_with_score(
            item["query"],
            k=k,
        )

        row = print_retrieval_results(
            query_id=item["id"],
            query=item["query"],
            results=results,
            expected_terms=item["expected_terms"],
        )

        summary_rows.append(row)

    return summary_rows


def print_markdown_baseline_table(summary_rows):
    """
    Print a markdown table that can be copied into chunking_experiment.md.
    """

    print("\n\n")
    print("# Markdown table for chunking_experiment.md")
    print()
    print("| # | Query | Top-1 Distance | Hit in Top-4? | Notes |")
    print("|---|-------|----------------|---------------|-------|")

    for index, row in enumerate(summary_rows, start=1):
        hit_text = "HIT" if row["hit"] else "MISS"
        distance = row["top_1_distance"]

        if distance is None:
            distance_text = ""
        else:
            distance_text = f"{distance:.6f}"

        query = row["query"].replace("|", "\\|")

        print(
            f"| {index} | {query} | {distance_text} | {hit_text} | {row['query_id']} |"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Inspect ChromaDB retrieval results for Homework 2."
    )

    parser.add_argument(
        "--store",
        default=str(DEFAULT_STORE_DIR),
        help="Path to ChromaDB store folder.",
    )

    parser.add_argument(
        "--k",
        type=int,
        default=DEFAULT_K,
        help="Number of chunks to retrieve.",
    )

    args = parser.parse_args()

    store_dir = Path(args.store)

    print(f"Store: {store_dir}")
    print(f"k: {args.k}")

    summary_rows = run_all_queries(
        store_dir=store_dir,
        k=args.k,
    )

    print_markdown_baseline_table(summary_rows)

    total_hits = sum(1 for row in summary_rows if row["hit"])
    total_queries = len(summary_rows)

    print()
    print(f"Hits: {total_hits}/{total_queries}")

    if total_hits == total_queries:
        print(
            "WARNING: All queries are HIT. "
            "Homework requires at least 1 MISS for the baseline. "
            "Consider making one or more questions harder."
        )


if __name__ == "__main__":
    main()