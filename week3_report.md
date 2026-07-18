# Week 3 Report — Agents that choose, measure, and remember


## Step 1 — Tool calling

Question:

> What is 18% of 2450?

Trajectory:

```python
{'tool': 'calculator', 'args': {'expression': '18% of 2450'}}
```

Final answer:

```text
18% of 2450 is 441.
```

This proves that the model selected `calculator` through a structured tool call, not by hand-parsed text.


## Step 2 — Routing evaluation

### Golden set

- R1: expected `calculator` — What is 18% of 2450?
- R2: expected `get_team` — Who manages the Platform team?
- R3: expected `get_employee` — What is Sarah Kim's email?
- R4: expected `search_docs` — According to our internal docs, what does the RAG checklist say about citations?
- R5: expected `search_web` — Search the web for public information about LangGraph checkpointing.
- R6: expected `search_docs` — According to our internal docs, what is our checkpoint policy for customer-facing agent workflows?
- R7: expected `search_web` — Find public web information about LangGraph checkpointing and interrupts.
- R8: expected `get_team` — What does our internal team directory say about the Platform team?

### Accuracy numbers

- Baseline accuracy: 8/8 = 1.00
- Broken accuracy: 4/8 = 0.50
- Fixed accuracy: 8/8 = 1.00

### Baseline failures

No failures.

### Broken failures

- R4: expected search_docs, got search_web
- R5: expected search_web, got search_docs
- R6: expected search_docs, got search_web
- R7: expected search_web, got search_docs

### Fixed failures

No failures.

### Description change

```text

Broken `search_docs` description:

Search public web pages, external documentation, current news, and internet information. Do not use this for private internal documents.

Fixed `search_docs` description:

Search ONLY internal/private company documents and private project notes. Use this when the user says 'internal docs', 'our docs', 'company policy', 'private notes', or asks about internal RAG, memory, checkpoint, or mail automation policy. Do NOT use this for public web or current external information.

Broken `search_web` description:

Search private internal company documents, internal policies, private notes, and team docs.

Fixed `search_web` description:

Search ONLY public/external web-style information. Use this when the user asks for public information, external docs, online information, recent news, or specifically says 'web'. Do NOT use this for internal company docs or private notes.

```


## Step 3 — Memory continuity

### Without memory

Turn 1:

User: Who manages the Platform team?

Assistant: The Platform team is managed by Sarah Kim.

Trajectory:

```python
{'tool': 'get_team', 'args': {'name': 'Platform'}}
```

Turn 2:

User: And her email?

Assistant: I do not have enough context to provide an email. Please specify the person's name.

Trajectory:

```python
No tool calls.
```

### With memory

Turn 1:

User: Who manages the Platform team?

Assistant: The Platform team is managed by Sarah Kim.

Trajectory:

```python
{'tool': 'get_team', 'args': {'name': 'Platform'}}
```

Assembled context before second turn:

```text
Recent turns:
Turn 1 user: Who manages the Platform team?
Turn 1 assistant: The Platform team is managed by Sarah Kim.
```

Turn 2:

User: And her email?

Assistant: Sarah Kim's email is sarah.kim@company.example.

Trajectory:

```python
{'tool': 'get_employee', 'args': {'name': 'Sarah Kim'}}
```

The assembled context contains `Sarah Kim`, which proves the application injected memory context before the second turn.


## Step 4 — Integration conversation

Routing accuracy:

5/5 = 1.00


### Turn 1

User:

Who manages the Platform team?

Assembled context:

```text
No previous conversation context.
```

Trajectory:

```python
{'tool': 'get_team', 'args': {'name': 'Platform'}}
```

Expected tool: `get_team`

Actual tool: `get_team`

Routing pass: `True`

Memory dependent: `False`

Assistant:

The Platform team is managed by Sarah Kim.


### Turn 2

User:

And her email?

Assembled context:

```text
Recent turns:
Turn 1 user: Who manages the Platform team?
Turn 1 assistant: The Platform team is managed by Sarah Kim.
```

Trajectory:

```python
{'tool': 'get_employee', 'args': {'name': 'Sarah Kim'}}
```

Expected tool: `get_employee`

Actual tool: `get_employee`

Routing pass: `True`

Memory dependent: `True`

Assistant:

Sarah Kim's email is sarah.kim@company.example.


### Turn 3

User:

What is 18% of 2450?

Assembled context:

```text
Recent turns:
Turn 1 user: Who manages the Platform team?
Turn 1 assistant: The Platform team is managed by Sarah Kim.
Turn 2 user: And her email?
Turn 2 assistant: Sarah Kim's email is sarah.kim@company.example.
```

Trajectory:

```python
{'tool': 'calculator', 'args': {'expression': '18% of 2450'}}
```

Expected tool: `calculator`

Actual tool: `calculator`

Routing pass: `True`

Memory dependent: `False`

Assistant:

18% of 2450 is 441.


### Turn 4

User:

According to our internal docs, what does the RAG checklist say about citations?

Assembled context:

```text
Recent turns:
Turn 1 user: Who manages the Platform team?
Turn 1 assistant: The Platform team is managed by Sarah Kim.
Turn 2 user: And her email?
Turn 2 assistant: Sarah Kim's email is sarah.kim@company.example.
Turn 3 user: What is 18% of 2450?
Turn 3 assistant: 18% of 2450 is 441.
```

Trajectory:

```python
{'tool': 'search_docs', 'args': {'query': 'RAG checklist citations'}}
```

Expected tool: `search_docs`

Actual tool: `search_docs`

Routing pass: `True`

Memory dependent: `False`

Assistant:

The RAG checklist states that answers must be grounded in retrieved context, include citations when sources are available, avoid unsupported claims, and say "I don't have information about that" when context is insufficient.


### Turn 5

User:

Search the web for public information about LangGraph checkpointing.

Assembled context:

```text
Recent turns:
Turn 1 user: Who manages the Platform team?
Turn 1 assistant: The Platform team is managed by Sarah Kim.
Turn 2 user: And her email?
Turn 2 assistant: Sarah Kim's email is sarah.kim@company.example.
Turn 3 user: What is 18% of 2450?
Turn 3 assistant: 18% of 2450 is 441.
Turn 4 user: According to our internal docs, what does the RAG checklist say about citations?
Turn 4 assistant: The RAG checklist states that answers must be grounded in retrieved context, include citations when sources are available, avoid unsupported claims, and say "I don't have information about that" when context is insufficient.
```

Trajectory:

```python
{'tool': 'search_web', 'args': {'query': 'LangGraph checkpointing'}}
```

Expected tool: `search_web`

Actual tool: `search_web`

Routing pass: `True`

Memory dependent: `False`

Assistant:

LangGraph is a framework designed for building stateful, multi-step LLM applications that incorporates features like graphs, persistence, checkpointing, and human-in-the-loop flows. Checkpointing specifically allows for saving the intermediate workflow state, enabling processes to pause, resume, or recover after interruptions.



## One analyzed failure

Failure selected from the intentionally broken routing run.

Question:

> According to our internal docs, what does the RAG checklist say about citations?

Expected tool:

`search_docs`

Actual tool:

`search_web`

Root cause:

The tool description was intentionally misleading. The model was instructed to trust tool descriptions, so it selected the wrong tool. This is a routing-layer failure, not a memory failure.

Fix:

Sharpen the tool descriptions so they clearly separate internal/private document search from public web search, and clearly separate person lookup from team lookup.

Result:

The fixed description run recovered the routing accuracy compared with the broken run.


## Final sentence

Memory was the more fragile layer conceptually, because follow-up questions only worked when the application explicitly injected the assembled context; without that context, the model could not resolve pronouns like 'her'.
