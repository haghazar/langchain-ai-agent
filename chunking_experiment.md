# Chunking Experiment Report

## 1. Frozen Query Set

These 10 queries are frozen for the whole chunking experiment.  
Each pair asks about the same fact in two different ways.

### Pair 1 — Public asset tracking

- A: How is an asset tracked in public chaincode state?
- B: What is publicly visible about the asset if its sensitive details are hidden?

Expected answer:
An asset is tracked by a UUID key in public chaincode state, and only ownership is recorded publicly.

---

### Pair 2 — Transfer endorsement

- A: Which organizations must endorse any transfer requests?
- B: Whose sign-off is required before the owner can hand the asset to someone else?

Expected answer:
A peer from the owner’s organization and a regulator’s organization must endorse transfer requests.

---

### Pair 3 — Seller proof of ownership

- A: How does the seller provide proof of ownership to the buyer?
- B: How can the buyer avoid simply trusting the seller’s word?

Expected answer:
The seller provides proof by passing private details out of band or by giving the buyer credentials to query the private data on their node or the regulator’s node.

---

### Pair 4 — Buyer bid details

- A: Where does the buyer record their bid details?
- B: Where is the buyer’s purchase proposal kept away from other channel members?

Expected answer:
The buyer records bid details in their own private data collection.

---

### Pair 5 — Chaincode verification before transfer

- A: What does the chaincode verify before transferring the asset?
- B: What validation happens before the asset leaves the seller’s side?

Expected answer:
The chaincode verifies that the submitting client is the owner, checks the private details against the hash in the seller’s collection, and checks the bid details against the hash in the buyer’s collection.

---

## 2. Baseline Results — 500/50

Hit/Miss rule: A query is marked as HIT only if the retrieved top-4 chunks contain the specific information required by the expected answer. Broadly related chunks are not enough.

| # | Query | Top-1 Distance | Hit in Top-4? | Notes |
|---|-------|----------------|---------------|-------|
| 1 | How is an asset tracked in public chaincode state? | 0.419946 | HIT | Q1A |
| 2 | What is publicly visible about the asset if its sensitive details are hidden? | 0.570928 | HIT | Q1B |
| 3 | Which organizations must endorse any transfer requests? | 0.650499 | HIT | Q2A |
| 4 | Whose sign-off is required before the owner can hand the asset to someone else? | 0.538275 | HIT | Q2B |
| 5 | How does the seller provide proof of ownership to the buyer? | 0.402773 | HIT | Q3A |
| 6 | How can the buyer avoid simply trusting the seller’s word? | 0.492686 | HIT | Q3B |
| 7 | Where does the buyer record their bid details? | 0.471085 | HIT | Q4A |
| 8 | Where is the buyer’s purchase proposal kept away from other channel members? | 0.540377 | HIT | Q4B |
| 9 | What does the chaincode verify before transferring the asset? | 0.427236 | HIT | Q5A |
| 10 | What validation happens before the asset leaves the seller’s side? | 0.451776 | MISS | Q5B |

Baseline result: 9/10 hits. Q5B missed because the retrieved top-4 chunks did not contain the exact chaincode verification details required by the expected answer.
---

## 3. Chunk Counts Per Strategy

| Strategy | Chunk Size | Overlap | Chunk Count |
|----------|------------|---------|-------------|
| baseline | 500 | 50 | 12 |
| lab_small | 200 | 20 | 31 |
| lab_large | 800 | 100 | 6 |
| lab_no_overlap | 500 | 0 | 12 |

---

## 4. Full Results Table

### Hits Summary

| Strategy | Hits out of 10 |
|----------|----------------|
| Baseline 500/50 | 9/10 |
| Small 200/20 | 8/10 |
| Large 800/100 | 9/10 |
| No Overlap 500/0 | 9/10 |

### Query-Level Results

| # | Query | Baseline 500/50 | Small 200/20 | Large 800/100 | No Overlap 500/0 |
|---|-------|------------------|---------------|----------------|------------------|
| 1 | How is an asset tracked in public chaincode state? | HIT / 0.419946 | HIT / 0.291364 | HIT / 0.436646 | HIT / 0.419946 |
| 2 | What is publicly visible about the asset if its sensitive details are hidden? | HIT / 0.570928 | HIT / 0.469495 | HIT / 0.643908 | HIT / 0.570928 |
| 3 | Which organizations must endorse any transfer requests? | HIT / 0.650499 | HIT / 0.283102 | HIT / 0.669220 | HIT / 0.650499 |
| 4 | Whose sign-off is required before the owner can hand the asset to someone else? | HIT / 0.538275 | HIT / 0.529338 | HIT / 0.571271 | HIT / 0.538275 |
| 5 | How does the seller provide proof of ownership to the buyer? | HIT / 0.402773 | HIT / 0.348388 | MISS / 0.573737 | HIT / 0.402773 |
| 6 | How can the buyer avoid simply trusting the seller’s word? | HIT / 0.492686 | HIT / 0.468575 | HIT / 0.619881 | HIT / 0.492686 |
| 7 | Where does the buyer record their bid details? | HIT / 0.471085 | HIT / 0.514886 | HIT / 0.571335 | HIT / 0.471085 |
| 8 | Where is the buyer’s purchase proposal kept away from other channel members? | HIT / 0.540377 | HIT / 0.563680 | HIT / 0.611922 | HIT / 0.540377 |
| 9 | What does the chaincode verify before transferring the asset? | HIT / 0.427236 | MISS / 0.410620 | HIT / 0.406051 | HIT / 0.427236 |
| 10 | What validation happens before the asset leaves the seller’s side? | MISS / 0.451776 | MISS / 0.468008 | HIT / 0.500859 | MISS / 0.451776 |

---

## 5. Winner

Winner: No Overlap 500/0

Justification:
My data is long, sequential explanatory prose about an asset-transfer workflow, not FAQ-like short answers or tables/code. The 500/0 strategy matched the baseline hit rate and distances without needing overlapping text, while the 800/100 strategy fixed Q5B but introduced a miss on another query.

---

## 6. Final Verification

- 3 answerable RAG questions: Passed. After rebuilding `chromadb_store/` with the winning 500/0 splitter, the RAG chain answered the asset tracking, endorsement, and chaincode verification questions from the private data.
- 1 out-of-domain question: "When was the Eiffel Tower built?"
- Hallucination guard result: Passed. The chain returned "I don't have information about that."
- Note: Gemini final verification was blocked by a 429 quota error, so the final RAG check was run with the same rebuilt ChromaDB store and the same hallucination-guard prompt using `gpt-4o-mini` as the chat model.

---

## 7. Experiment Finding

Final finding:
The experiment found a chunking-related failure: Q5B flipped from MISS under the baseline 500/50 strategy to HIT under the large 800/100 strategy. However, large chunks also caused another query to miss, so the best overall strategy by the assignment rule was No Overlap 500/0.