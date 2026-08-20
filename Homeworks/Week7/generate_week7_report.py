from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TRANSCRIPT_PATH = BASE_DIR / "outputs" / "week7_pipeline_transcript.txt"
REPORT_PATH = BASE_DIR / "week7_report.md"
FENCE = "`" * 3


def md_code_block(text: str, language: str = "text") -> str:
    return f"{FENCE}{language}\n{text}\n{FENCE}"


def read_transcript() -> str:
    if not TRANSCRIPT_PATH.exists():
        return "Transcript file was not found. Run the pipeline first."

    encodings = [
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "cp1251",
    ]

    for encoding in encodings:
        try:
            return TRANSCRIPT_PATH.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    return TRANSCRIPT_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )


def generate_report() -> str:
    transcript = read_transcript()

    return f"""# Week 7 Report — Multi-Agent Pipeline

## 1. Goal

The goal of this lab was to build a multi-agent system where the graph topology coordinates the agents instead of a manual `while` loop.

The implemented topology is:

{md_code_block("orchestrator -> parallel workers -> writer -> reviewer")}

If the reviewer rejects the draft, the graph routes back to the writer. If the reviewer approves, or the maximum revision limit is reached, the graph ends.

## 2. Implemented agent roles

The pipeline includes four different agent roles.

### 2.1 Orchestrator

The orchestrator receives the original user question and decomposes it into 2-4 focused, independent sub-questions.

Implemented behavior:

- Uses structured output with the `SubQuestions` Pydantic schema.
- Returns `sub_questions` into the graph state.
- Initializes `findings` as an empty list.

### 2.2 Worker

Each worker receives exactly one sub-question through `WorkerState`.

Implemented behavior:

- Does not see the full graph state.
- Answers only its assigned sub-question.
- Returns one finding in this shape:

{md_code_block('{"findings": [{"sub_question": "...", "answer": "..."}]}', "python")}

This is important because `findings` uses `operator.add`, so parallel worker results are merged safely.

### 2.3 Writer

The writer synthesizes all worker findings into one draft.

Implemented behavior:

- Creates the first draft when there is no reviewer feedback.
- Creates a revised draft when reviewer feedback exists.
- Increments `revision_count` only when producing a revision.

### 2.4 Reviewer

The reviewer judges the draft against the original question.

Implemented behavior:

- Uses structured output with the `ReviewVerdict` Pydantic schema.
- Returns `approved=True` and empty feedback when the draft is good enough.
- Returns `approved=False` and actionable feedback when the draft needs revision.

## 3. Routing and graph design

### 3.1 Fan-out

The `assign_workers` function returns one `Send` object per sub-question.

This creates dynamic parallel worker execution:

{md_code_block('Send("worker", {"sub_question": sub_question})', "python")}

### 3.2 Fan-in

All workers write into `findings`.

Because `findings` is declared as:

{md_code_block("findings: Annotated[List[dict], operator.add]", "python")}

the graph merges all worker outputs into one list.

### 3.3 Review loop

The `route_after_review` function returns:

- `"end"` if the draft is approved.
- `"revise"` if the draft is rejected and revision limit is not reached.
- `"end"` if the maximum revision limit is reached.

The graph maps those routing labels to:

{md_code_block('{"revise": "writer", "end": END}', "python")}

## 4. Tests

Before running the full LLM pipeline, I tested the plain Python routing functions.

Tested functions:

- `assign_workers`
- `route_after_review`

Selftest result:

{md_code_block("""WEEK 7 SELFTEST
TEST 1 PASSED: assign_workers creates one Send per sub-question
TEST 2 PASSED: route_after_review routes correctly
ALL WEEK 7 SELFTESTS PASSED""")}

This avoided wasting model calls while debugging non-LLM logic.

## 5. Real pipeline run

The full graph was executed once and the transcript was saved.

Command used:

{md_code_block("python .\\Homeworks\\Week7\\Week7_Lab_Pipeline_Skeleton.py | Tee-Object .\\Homeworks\\Week7\\outputs\\week7_pipeline_transcript.txt", "powershell")}

Observed transcript:

{md_code_block(transcript)}

## 6. Result interpretation

The real run produced:

- 4 worker findings
- 0 revisions
- reviewer approval: True

This means the orchestrator created four sub-questions, four workers returned findings, the writer synthesized those findings, and the reviewer approved the first draft without requiring a revision.

## 7. Design choices

### Revision count

I incremented `revision_count` inside the writer node only when reviewer feedback exists.

Reason:

The first draft should not count as a revision. A revision only happens after the reviewer rejects a draft and sends feedback back to the writer.

### Worker isolation

Each worker receives only `WorkerState`, not the full `State`.

Reason:

This preserves the lab's design: each worker answers one sub-question blindly and independently.

### Lazy LLM initialization

The LLM is created lazily through `get_llm()`.

Reason:

This allows selftests to import the module and test plain Python routing functions without triggering model calls.

## 8. Limitation

The current implementation does not include production-grade error handling.

For a real production version, I would add:

- retry logic around LLM calls,
- structured logging,
- timeout handling,
- validation of empty worker findings,
- fallback behavior if the reviewer repeatedly rejects the draft.

The lab instructions said not to overbuild real error handling, so I kept the implementation focused on the graph topology.

## 9. Final conclusion

The Week 7 pipeline successfully demonstrates a multi-agent LangGraph architecture where topology coordinates the work: the orchestrator decomposes the problem, workers run in parallel, the writer synthesizes the result, and the reviewer either approves or loops the draft back for revision.
"""


def main() -> None:
    report = generate_report()

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print("=" * 100)
    print("WEEK 7 REPORT GENERATED")
    print("=" * 100)
    print(f"Report path: {REPORT_PATH}")
    print("=" * 100)


if __name__ == "__main__":
    main()