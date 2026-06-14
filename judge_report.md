# Judge Report

## 1. Baseline Answer Evaluation

The LLM judge evaluated 10 in-domain RAG answers from the golden query set.

A score of 4 or 5 was treated as pass. A score of 1, 2, or 3 was treated as fail.

* Faithfulness pass-rate: 7/10 = 0.70
* Correctness pass-rate: 7/10 = 0.70

The failed items were Q1B, Q2B, and Q5B. These cases will be useful for judge calibration and disagreement analysis.


## 2. Human Calibration

I manually graded the same 10 RAG answers using two yes/no labels:

* Faithful: whether every claim in the answer is supported by the retrieved context.
* Correct: whether the answer matches the reference answer in meaning.

A judge score of 4 or 5 was treated as pass. A score of 1, 2, or 3 was treated as fail.

| ID  | Judge Faithful | Human Faithful | Judge Correct | Human Correct |
| --- | -------------- | -------------- | ------------- | ------------- |
| Q1A | yes            | yes            | yes           | yes           |
| Q1B | no             | yes            | no            | yes           |
| Q2A | yes            | yes            | yes           | yes           |
| Q2B | no             | yes            | no            | no            |
| Q3A | yes            | yes            | yes           | yes           |
| Q3B | yes            | yes            | yes           | yes           |
| Q4A | yes            | yes            | yes           | yes           |
| Q4B | yes            | yes            | yes           | yes           |
| Q5A | yes            | yes            | yes           | yes           |
| Q5B | no             | yes            | no            | no            |

Agreement results:

* Faithfulness agreement: 7/10 = 0.70
* Correctness agreement: 9/10 = 0.90
* Overall label agreement: 16/20 = 0.80

The overall judge-human agreement rate is 0.80.


## 3. Disagreement Analysis

Disagreement case: Q1B

Question:

> What is publicly visible about the asset if its sensitive details are hidden?

RAG answer:

> The asset's ownership is recorded, and other channel members interested in the asset may query the history of the public key to understand its provenance, but will not have access to any private details unless an owner shares it on a need-to-know basis.

Judge verdict:

* Faithfulness: fail
* Correctness: fail

Human verdict:

* Faithfulness: pass
* Correctness: pass

Cause:

The judge was too strict and treated extra but relevant context-supported detail as an error because it was not included in the short reference answer.


## 4. Verbosity Bias Stress Test

I tested the judge on the same question with one concise correct answer and one verbose but still correct answer.

Question:

> Which organizations must endorse any transfer requests?

Concise answer:

> A peer from the owner’s organization and a regulator’s organization must endorse any transfer requests.

Verbose answer:

> A transfer request must be endorsed by a peer from the owner’s organization and by a regulator’s organization. In other words, both the owner’s side and the regulator’s side need to sign off before the asset can be transferred. This is the required approval path for the transfer request.

Scores:

| Answer Type | Faithfulness Score | Correctness Score |
| ----------- | -----------------: | ----------------: |
| Concise     |                  5 |                 5 |
| Verbose     |                  5 |                 5 |

Result:

No verbosity bias appeared. The verbose answer did not receive a higher score than the concise answer.


## 5. Trust Statement

I partially trust this judge's numbers because the overall agreement with my human labels was 0.80, but I do not fully trust it because the Q1B disagreement showed that it can be too strict when an answer includes extra but relevant context-supported detail.