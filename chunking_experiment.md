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
| baseline | 500 | 50 |  |
| lab_small | 200 | 20 |  |
| lab_large | 800 | 100 |  |
| lab_no_overlap | 500 | 0 |  |

---

## 4. Full Results Table

| # | Query | Baseline 500/50 | Small 200/20 | Large 800/100 | No Overlap 500/0 |
|---|-------|------------------|---------------|----------------|------------------|
| 1 | How is an asset tracked in public chaincode state? |  |  |  |  |
| 2 | What is publicly visible about the asset if its sensitive details are hidden? |  |  |  |  |
| 3 | Which organizations must endorse any transfer requests? |  |  |  |  |
| 4 | Whose sign-off is required before the owner can hand the asset to someone else? |  |  |  |  |
| 5 | How does the seller provide proof of ownership to the buyer? |  |  |  |  |
| 6 | How can the buyer avoid simply trusting the seller’s word? |  |  |  |  |
| 7 | Where does the buyer record their bid details? |  |  |  |  |
| 8 | Where is the buyer’s purchase proposal kept away from other channel members? |  |  |  |  |
| 9 | What does the chaincode verify before transferring the asset? |  |  |  |  |
| 10 | What validation happens before the asset leaves the seller’s side? |  |  |  |  |

---

## 5. Winner

Winner:

Justification:

---

## 6. Final Verification

- 3 answerable RAG questions:
- 1 out-of-domain question:
- Hallucination guard result:

---

## 7. Experiment Finding

Final finding:
