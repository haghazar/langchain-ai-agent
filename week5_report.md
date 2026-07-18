# Week 5 Report — From Scripts to Classes + the Email Agent


## 1. Architecture overview

For Week 5, I refactored the flat script-style agent into object-oriented components.

The class-based implementation is separated into these components:

- `ToolRegistry` owns tool data, tool descriptions, and tool construction.
- `ToolCallingAgent` owns the LLM, tools, tool map, max step configuration, and trajectory.
- `ConversationMemory` owns recent turns and rolling summary.
- `ChatSession` owns a `ToolCallingAgent`, a `ConversationMemory`, and the transcript.
- `RoutingEvaluator` owns the golden set and routing evaluation results.
- `EmailMemoryStore` owns semantic, episodic, and procedural memory.
- `EmailTriageRouter` owns email triage behavior.
- `EmailResponseAgent` owns reply drafting behavior.
- `EmailAssistant` composes the memory store, triage router, and response agent.

This demonstrates encapsulation because state is owned by classes instead of module-level global variables.


## 2. Composition proof

The email assistant is assembled using composition:

```text
EmailAssistant
├── has-a EmailMemoryStore
├── has-a EmailTriageRouter
└── has-a EmailResponseAgent
```

`EmailAssistant` does not inherit from the memory store, router, or response agent. It receives ready instances and orchestrates them.

This means the memory implementation can be swapped later. For example, `EmailMemoryStore` could be replaced with a Chroma-backed store without rewriting the triage router or response agent.


## 3. Behavior-preserving refactor

A refactor should preserve behavior, not merely rewrite code in a new style.

The class-based version was compared against the previous flat script behavior where possible.

| Test | Old flat script | New class-based version | Match |
|---|---|---|---|
| Calculator | `calculator` → 18% of 2450 is 441. | `calculator` → 18% of 2450 is 441. | True |
| Platform manager | `get_team` → The Platform team is managed by Sarah Kim. | `get_team` → The Platform team is managed by Sarah Kim. | True |

New class-based calculator trajectory:

```python
{'tool': 'calculator', 'args': {'expression': '0.18 * 2450'}}
```

New class-based calculator final answer:

```text
18% of 2450 is 441.
```


## 4. Tool calling and routing measurement

### Structured tool calling proof

Question:

> What is 18% of 2450?

Trajectory:

```python
{'tool': 'calculator', 'args': {'expression': '0.18 * 2450'}}
```

Final answer:

```text
18% of 2450 is 441.
```

The trajectory shows that the model selected `calculator` through a structured tool call.

### Routing accuracy

Routing accuracy:

```text
8/8 = 1.00
```

| ID | Expected tool | Actual tool | Pass |
|---|---|---|---|
| R1 | calculator | calculator | True |
| R2 | get_team | get_team | True |
| R3 | get_employee | get_employee | True |
| R4 | search_docs | search_docs | True |
| R5 | search_web | search_web | True |
| R6 | search_docs | search_docs | True |
| R7 | search_web | search_web | True |
| R8 | get_team | get_team | True |


## 5. Conversation memory proof

The follow-up question works because the application injects assembled memory context into the next turn.

### Turn 1

User:

```text
Who manages the Platform team?
```

Assistant:

```text
The Platform team is managed by Sarah Kim.
```

Trajectory:

```python
{'tool': 'get_team', 'args': {'name': 'Platform'}}
```

### Assembled context before Turn 2

```text
Recent turns:
Turn 1 user: Who manages the Platform team?
Turn 1 assistant: The Platform team is managed by Sarah Kim.
```

The assembled context contains `Sarah Kim`.

### Turn 2

User:

```text
And her email?
```

Assistant:

```text
Sarah Kim's email is sarah.kim@company.example.
```

Trajectory:

```python
{'tool': 'get_employee', 'args': {'name': 'Sarah Kim'}}
```

This proves that the follow-up resolved `her` from injected memory context.


## 6. Email agent memory acts

### 6.1 Semantic memory

Stored fact:

```text
Hayk prefers concise, warm, professional email replies.
```

Recall with no email in sight:

```text
- Hayk prefers concise, warm, professional email replies.
```

This proves semantic memory stores and recalls stable facts.

### 6.2 Episodic memory

Before adding one episodic example:

```text
Action: archive
Reason: No reply-required signal found.
Memory used: rule
```

Then one example was stored:

```text
Email: Just checking if there are any updates.
Decision: reply
Reason: A follow-up from an important client should receive an acknowledgment.
```

After adding the episodic example:

```text
Action: reply
Reason: Decision influenced by similar episodic memory: A follow-up from an important client should receive an acknowledgment.
Memory used: episodic
```

The same email changed from `archive` to `reply` without changing a hard-coded rule. The decision changed because an episodic memory was retrieved.

### 6.3 Procedural memory

Procedural instructions before feedback:

```text
- Never send emails automatically.
- Always create a Gmail draft and require human review before sending.
- Use a concise, professional tone.
```

Feedback applied:

```text
Use a formal banking tone and avoid casual phrases.
```

Procedural instructions after feedback:

```text
- Never send emails automatically.
- Always create a Gmail draft and require human review before sending.
- Use a formal banking tone and avoid casual phrases.
```

Reloaded procedural instructions from JSON:

```text
- Never send emails automatically.
- Always create a Gmail draft and require human review before sending.
- Use a formal banking tone and avoid casual phrases.
```

Draft after procedural feedback:

Subject:

```text
Re: Loan payment question
```

Body:

```text
Dear colleague,

Thank you for your email.

I have reviewed your message and will follow up accordingly. If any additional information is required, I will let you know.

Style memory applied: Hayk prefers concise, warm, professional email replies. Procedural instructions applied: Never send emails automatically.; Always create a Gmail draft and require human review before sending.; Use a formal banking tone and avoid casual phrases.

Best regards,
Hayk
```

This proves procedural feedback permanently rewrote the stored instructions in `email_memory_store.json`.


## 7. Real Gmail draft-only integration

The Gmail integration was implemented in `week5_gmail_client.py`.

The Gmail client supports:

```text
list_recent_messages()
create_draft_reply()
```

It intentionally does not implement:

```text
send_email()
send_draft()
```

A real Gmail draft was created during testing with `test_email_agent_gmail_draft.py`.

Observed test output:

```text
REAL GMAIL DRAFT CREATED BY EMAIL ASSISTANT
The email was saved as a Gmail draft only. It was not sent.
```

This proves that the email agent can create a real Gmail draft while preserving the safety rule: no automatic sending.


## 8. Automated test results

The Week 5 core test file `test_week5_homework.py` was executed successfully.

```text
TEST 1: STRUCTURED TOOL CALLING - PASSED
TEST 2: CLASS-BASED MEMORY FOLLOW-UP - PASSED
TEST 3: ROUTING EVALUATOR - PASSED
TEST 4: SEMANTIC MEMORY - PASSED
TEST 5: EPISODIC MEMORY FLIPS TRIAGE DECISION - PASSED
TEST 6: PROCEDURAL MEMORY PERSISTENCE - PASSED
ALL WEEK 5 CORE TESTS PASSED
```

This confirms that the class-based agent, routing evaluator, memory follow-up, and all three email memory types work end-to-end.


## 9. One analyzed failure / limitation

The most important limitation is that the current email triage logic uses simple keyword overlap for episodic memory retrieval.

Root cause:

A keyword-overlap matcher can miss semantically similar emails if they use different words. For example, an email saying "Could you update me?" may be similar to "Just checking if there are any updates", but the overlap score may be weak.

Fix:

The memory store is encapsulated behind `EmailMemoryStore`, so the implementation can be swapped later. A Chroma-backed vector store can replace the simple JSON keyword matching without changing `EmailAssistant`, `EmailTriageRouter`, or `EmailResponseAgent`.

This is exactly why the design uses composition.


## 10. Final sentence

Memory was the more fragile layer in my agent, because follow-up questions and email triage decisions only worked when the application explicitly injected or retrieved the right memory; routing was more stable after tool descriptions were made clear.
