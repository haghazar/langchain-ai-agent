# Chunking Experiment Report

## 1. Frozen Query Set

These 10 queries are frozen for the whole chunking experiment.  
Each pair asks about the same fact in two different ways.

### Pair 1 — Public asset tracking

- A: How is an asset tracked in public chaincode state?
- B: What public identifier is used to record the asset?

Expected answer:
An asset is tracked by a UUID key in public chaincode state, and only ownership is recorded publicly.

---

### Pair 2 — Transfer endorsement

- A: Which organizations must endorse any transfer requests?
- B: Who needs to approve the asset transfer before it is accepted?

Expected answer:
A peer from the owner’s organization and a regulator’s organization must endorse transfer requests.

---

### Pair 3 — Seller proof of ownership

- A: How does the seller provide proof of ownership to the buyer?
- B: How can the buyer confirm that the seller really owns the asset?

Expected answer:
The seller provides proof by passing private details out of band or by giving the buyer credentials to query the private data on their node or the regulator’s node.

---

### Pair 4 — Buyer bid details

- A: Where does the buyer record their bid details?
- B: Where is the buyer’s offer information stored privately?

Expected answer:
The buyer records bid details in their own private data collection.

---

### Pair 5 — Chaincode verification before transfer

- A: What does the chaincode verify before transferring the asset?
- B: What checks are performed before ownership is moved to the buyer?

Expected answer:
The chaincode verifies that the submitting client is the owner, checks the private details against the hash in the seller’s collection, and checks the bid details against the hash in the buyer’s collection.

---

## 2. Baseline Results — 500/50

| # | Query | Top-1 Distance | Hit in Top-4? | Notes |
|---|-------|----------------|---------------|-------|
| 1 |       |                |               |       |
| 2 |       |                |               |       |
| 3 |       |                |               |       |
| 4 |       |                |               |       |
| 5 |       |                |               |       |
| 6 |       |                |               |       |
| 7 |       |                |               |       |
| 8 |       |                |               |       |
| 9 |       |                |               |       |
| 10 |      |                |               |       |

---

## 3. Chunk Counts Per Strategy

| Strategy | Chunk Size | Overlap | Chunk Count |
|----------|------------|---------|-------------|
| baseline | 500 | 50 | |
| lab_small | 200 | 20 | |
| lab_large | 800 | 100 | |
| lab_no_overlap | 500 | 0 | |

---

## 4. Full Results Table

| # | Query | Baseline 500/50 | Small 200/20 | Large 800/100 | No Overlap 500/0 |
|---|-------|------------------|---------------|----------------|------------------|
| 1 |       |                  |               |                |                  |
| 2 |       |                  |               |                |                  |
| 3 |       |                  |               |                |                  |
| 4 |       |                  |               |                |                  |
| 5 |       |                  |               |                |                  |
| 6 |       |                  |               |                |                  |
| 7 |       |                  |               |                |                  |
| 8 |       |                  |               |                |                  |
| 9 |       |                  |               |                |                  |
| 10 |      |                  |               |                |                  |

---

## 5. Winner

Winner:

Justification:

---

## 6. Final Verification

- 3 answerable RAG questions:
- 1 out-of-domain question:
- Hallucination guard result: