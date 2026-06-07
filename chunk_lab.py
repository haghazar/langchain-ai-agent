from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingest import build_store
from inspect_retrieval import FROZEN_QUERIES
from inspect_retrieval import create_vector_store
from inspect_retrieval import is_hit


STORES = [
    {
        "name": "baseline",
        "label": "Baseline 500/50",
        "persist_dir": Path("chromadb_store"),
        "chunk_size": 500,
        "chunk_overlap": 50,
        "build": False,
    },
    {
        "name": "lab_small",
        "label": "Small 200/20",
        "persist_dir": Path("lab_small"),
        "chunk_size": 200,
        "chunk_overlap": 20,
        "build": True,
    },
    {
        "name": "lab_large",
        "label": "Large 800/100",
        "persist_dir": Path("lab_large"),
        "chunk_size": 800,
        "chunk_overlap": 100,
        "build": True,
    },
    {
        "name": "lab_no_overlap",
        "label": "No Overlap 500/0",
        "persist_dir": Path("lab_no_overlap"),
        "chunk_size": 500,
        "chunk_overlap": 0,
        "build": True,
    },
]


def build_lab_stores():
    """
    Build lab ChromaDB stores for Homework 2.

    Baseline store is not rebuilt here because it is the original store:
    chromadb_store/ with chunk_size=500 and overlap=50.
    """

    chunk_counts = []

    for store in STORES:
        if not store["build"]:
            print("=" * 80)
            print(f"Skipping build for baseline store: {store['name']}")
            print(f"Persist directory: {store['persist_dir']}")
            print("=" * 80)
            print()
            continue

        print("=" * 80)
        print(f"Building store: {store['name']}")
        print(f"Chunk size: {store['chunk_size']}")
        print(f"Chunk overlap: {store['chunk_overlap']}")
        print(f"Persist directory: {store['persist_dir']}")
        print("=" * 80)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=store["chunk_size"],
            chunk_overlap=store["chunk_overlap"],
        )

        chunk_count = build_store(
            splitter=splitter,
            persist_dir=store["persist_dir"],
        )

        chunk_counts.append(
            {
                "strategy": store["name"],
                "chunk_size": store["chunk_size"],
                "chunk_overlap": store["chunk_overlap"],
                "chunk_count": chunk_count,
            }
        )

        print()

    return chunk_counts


def print_chunk_count_table(chunk_counts):
    """
    Print markdown table for chunking_experiment.md.
    """

    print("\n")
    print("# Chunk Counts Per Strategy")
    print()
    print("| Strategy | Chunk Size | Overlap | Chunk Count |")
    print("|----------|------------|---------|-------------|")

    for row in chunk_counts:
        print(
            f"| {row['strategy']} | "
            f"{row['chunk_size']} | "
            f"{row['chunk_overlap']} | "
            f"{row['chunk_count']} |"
        )


def evaluate_store(store, k=4):
    """
    Run all frozen queries against one ChromaDB store.

    Returns:
        results_by_query_id:
            {
                "Q1A": {
                    "query": "...",
                    "hit": True,
                    "top_1_distance": 0.123
                }
            }
    """

    store_dir = store["persist_dir"]

    if not store_dir.exists():
        raise FileNotFoundError(
            f"{store_dir} does not exist. Build the store first."
        )

    vector_store = create_vector_store(store_dir)

    results_by_query_id = {}

    for item in FROZEN_QUERIES:
        query_id = item["id"]
        query = item["query"]
        expected_terms = item["expected_terms"]

        results = vector_store.similarity_search_with_score(
            query,
            k=k,
        )

        top_1_distance = results[0][1] if results else None
        hit = is_hit(results, expected_terms) if results else False

        results_by_query_id[query_id] = {
            "query": query,
            "hit": hit,
            "top_1_distance": top_1_distance,
        }

    return results_by_query_id


def run_experiment(k=4):
    """
    Run the same frozen 10 queries against all 4 stores.
    """

    all_results = {}

    for store in STORES:
        print("=" * 80)
        print(f"Evaluating store: {store['name']}")
        print(f"Label: {store['label']}")
        print(f"Directory: {store['persist_dir']}")
        print("=" * 80)

        store_results = evaluate_store(
            store=store,
            k=k,
        )

        all_results[store["name"]] = store_results

        hits = sum(1 for result in store_results.values() if result["hit"])
        total = len(store_results)

        print(f"Hits: {hits}/{total}")
        print()

    return all_results


def format_cell(result):
    """
    Format one table cell as HIT/MISS with top-1 distance.
    """

    hit_text = "HIT" if result["hit"] else "MISS"
    distance = result["top_1_distance"]

    if distance is None:
        return f"{hit_text} / N/A"

    return f"{hit_text} / {distance:.6f}"


def print_summary_table(all_results):
    """
    Print hits out of 10 per strategy.
    """

    print("\n")
    print("# Hits Summary")
    print()
    print("| Strategy | Hits out of 10 |")
    print("|----------|----------------|")

    for store in STORES:
        store_name = store["name"]
        store_results = all_results[store_name]

        hits = sum(1 for result in store_results.values() if result["hit"])
        total = len(store_results)

        print(f"| {store['label']} | {hits}/{total} |")


def print_full_results_table(all_results):
    """
    Print markdown table:
    10 queries x 4 strategies.
    """

    print("\n")
    print("# Full Results Table")
    print()
    print(
        "| # | Query | Baseline 500/50 | Small 200/20 | Large 800/100 | No Overlap 500/0 |"
    )
    print(
        "|---|-------|------------------|---------------|----------------|------------------|"
    )

    for index, item in enumerate(FROZEN_QUERIES, start=1):
        query_id = item["id"]
        query = item["query"].replace("|", "\\|")

        baseline_cell = format_cell(all_results["baseline"][query_id])
        small_cell = format_cell(all_results["lab_small"][query_id])
        large_cell = format_cell(all_results["lab_large"][query_id])
        no_overlap_cell = format_cell(all_results["lab_no_overlap"][query_id])

        print(
            f"| {index} | {query} | "
            f"{baseline_cell} | "
            f"{small_cell} | "
            f"{large_cell} | "
            f"{no_overlap_cell} |"
        )


def main():
    """
    Homework 2 chunking experiment runner.

    This script:
    1. builds lab stores;
    2. runs the same 10 frozen queries against all stores;
    3. prints hits summary;
    4. prints full markdown results table for the report.
    """

    chunk_counts = build_lab_stores()
    print_chunk_count_table(chunk_counts)

    all_results = run_experiment(k=4)

    print_summary_table(all_results)
    print_full_results_table(all_results)


if __name__ == "__main__":
    main()