# Week 7 Report — Multi-Agent Pipeline

## 1. Goal

The goal of this lab was to build a multi-agent system where the graph topology coordinates the agents instead of a manual `while` loop.

The implemented topology is:

```text
orchestrator -> parallel workers -> writer -> reviewer
```

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

```python
{"findings": [{"sub_question": "...", "answer": "..."}]}
```

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

```python
Send("worker", {"sub_question": sub_question})
```

### 3.2 Fan-in

All workers write into `findings`.

Because `findings` is declared as:

```python
findings: Annotated[List[dict], operator.add]
```

the graph merges all worker outputs into one list.

### 3.3 Review loop

The `route_after_review` function returns:

- `"end"` if the draft is approved.
- `"revise"` if the draft is rejected and revision limit is not reached.
- `"end"` if the maximum revision limit is reached.

The graph maps those routing labels to:

```python
{"revise": "writer", "end": END}
```

## 4. Tests

Before running the full LLM pipeline, I tested the plain Python routing functions.

Tested functions:

- `assign_workers`
- `route_after_review`

Selftest result:

```text
WEEK 7 SELFTEST
TEST 1 PASSED: assign_workers creates one Send per sub-question
TEST 2 PASSED: route_after_review routes correctly
ALL WEEK 7 SELFTESTS PASSED
```

This avoided wasting model calls while debugging non-LLM logic.

## 5. Real pipeline run

The full graph was executed once and the transcript was saved.

Command used:

```powershell
python .\Homeworks\Week7\Week7_Lab_Pipeline_Skeleton.py | Tee-Object .\Homeworks\Week7\outputs\week7_pipeline_transcript.txt
```

Observed transcript:

```text

workers that reported: 4
revisions: 0  approved: True

--- DRAFT ---
For a small team, the decision of whether to consolidate accounting integrations into a single service or distribute them across several distinct services involves a trade-off between simplicity and resilience.

**Recommendation:**
For most small teams, **consolidating accounting integrations behind a single service is generally the more practical and cost-effective approach initially.** This prioritizes ease of management, lower operational costs, and faster setup, which are critical for teams with limited resources. However, it's crucial to be aware of and mitigate the significant risks associated with this approach.

Here's a breakdown of the considerations:

### Option 1: Consolidating into a Single Service

**Advantages for a Small Team:**

*   **Simplified Management & Lower Costs:** With limited IT staff, managing one service is significantly easier than juggling multiple. This reduces development, maintenance, and troubleshooting efforts, leading to lower operational expenses.
*   **Improved Data Consistency:** A single service can enforce uniform data transformation and synchronization rules, reducing the likelihood of discrepancies across your accounting systems.
*   **Enhanced Security & Monitoring:** A single point of control simplifies security measures, auditing, and provides a unified view of data flow, errors, and performance.
*   **Faster Onboarding:** Integrating new accounting systems or features can be quicker as you're working within a single, established framework.

**Potential Disadvantages & Risks:**

*   **Single Point of Failure:** This is the most critical risk. If the single service experiences an outage or technical issue, all your accounting integrations will be disrupted simultaneously, potentially halting critical financial operations.
*   **Vendor Lock-in:** Relying on one provider can make switching difficult and costly in the future, limiting your flexibility and potentially leading to higher long-term expenses if the vendor's terms change or their roadmap doesn't align with your needs.
*   **Security Risk Concentration:** A breach in this single service could compromise all your integrated accounting data at once.
*   **Limited Specialization:** The service might not offer the most tailored features for every specific accounting system or unique integration need compared to specialized tools.

### Option 2: Distributing Across Several Distinct Services

**Advantages:**

*   **Enhanced Fault Isolation:** A failure in one integration service won't necessarily impact others, allowing critical systems to remain operational.
*   **Improved Scalability:** Each service can be scaled independently based on its specific load, which can be beneficial as your team and integration needs grow.
*   **Modularity & Maintainability:** Developing, testing, and deploying changes to individual integrations is easier without affecting the entire system.

**Potential Disadvantages & Risks for a Small Team:**

*   **Increased Complexity:** Managing multiple services, each with its own configurations, monitoring, and deployment cycles, significantly increases operational complexity. This can quickly overwhelm a small team.
*   **Higher Costs:** More services typically mean higher development, hosting, and maintenance costs.
*   **Potential for Data Inconsistencies:** Without a centralized logic layer, ensuring uniform data across disparate services becomes more challenging and prone to errors.
*   **Higher Security Management Burden:** Managing security across multiple services, each with its own access points and configurations, increases the attack surface and the effort required for robust security.
*   **Challenging Troubleshooting:** Diagnosing issues across multiple interconnected services can be significantly more difficult and time-consuming.

### Conclusion for a Small Team:

While distributing integrations offers resilience and modularity, the **increased complexity, higher costs, and greater management burden** typically outweigh these benefits for a small team.

A single service provides the much-needed simplicity and cost-efficiency. To mitigate the "single point of failure" risk, a small team should:
1.  **Choose a reputable and reliable service provider** with a strong uptime record and robust security.
2.  **Implement clear backup and recovery strategies** for critical data.
3.  **Have contingency plans** for manual data entry or alternative processes in case of a service outage.

As the team grows and its integration needs become more complex and critical, re-evaluating a distributed architecture might become necessary. But for starting out, simplicity often wins.

```

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
