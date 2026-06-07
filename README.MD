# HaykAiAgent

HaykAiAgent is a simple RAG application built with LangChain, Google Gemini embeddings, ChromaDB, and a chat model.

The goal of the project is to load private documents, split them into chunks, store them in ChromaDB, and answer questions only from the retrieved context.

## Features

- Load private documents from the `data/` folder
- Support `.txt`, `.md`, and `.pdf` files
- Split documents with `RecursiveCharacterTextSplitter`
- Generate embeddings with Google Generative AI embeddings
- Store vectors in ChromaDB
- Build a RAG chain with LCEL
- Use a hallucination guard:
  - If the answer is not in the context, the assistant says:
    `"I don't have information about that."`
- Run chunking experiments with different chunk sizes and overlaps

## Project Structure

```text
HaykAiAgent/
│
├── data/                    # Private local documents, not pushed to GitHub
├── chromadb_store/          # Main ChromaDB vector store, not pushed to GitHub
├── lab_small/               # Experiment store, not pushed to GitHub
├── lab_large/               # Experiment store, not pushed to GitHub
├── lab_no_overlap/          # Experiment store, not pushed to GitHub
│
├── config.py                # Loads API keys from .env
├── test_connection.py       # Tests LLM, embeddings, and cosine similarity
├── ingest.py                # Loads, splits, embeds, and stores documents
├── rag.py                   # RAG chain with hallucination guard
├── inspect_retrieval.py     # Inspects top-k retrieved chunks and distances
├── chunk_lab.py             # Runs chunking experiments
├── chunking_experiment.md   # Final chunking experiment report
│
├── .env                     # API keys, not pushed to GitHub
├── .gitignore
└── README.md
```

## Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

Do not push `.env` to GitHub.

## Installation

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install required packages:

```powershell
python -m pip install -U langchain langchain-community langchain-text-splitters langchain-chroma chromadb pypdf python-dotenv langchain-google-genai langchain-openai
```

## Test the Connection

Run:

```powershell
python test_connection.py
```

This checks:

- API keys are loaded
- Chat model works
- Embeddings are generated
- Cosine similarity works correctly

## Prepare Private Data

Put your private `.txt`, `.md`, or `.pdf` files into the `data/` folder.

The `data/` folder is ignored by Git, so private files are not pushed to GitHub.

## Ingest Documents

Run:

```powershell
python ingest.py
```

This loads documents from `data/`, splits them into chunks, embeds them, and stores them in:

```text
chromadb_store/
```

Default chunking settings:

```text
chunk_size = 500
chunk_overlap = 50
```

## Run the RAG Chain

Run:

```powershell
python rag.py
```

The RAG chain answers questions only from retrieved context.

If the answer is not available in the context, it returns:

```text
I don't have information about that.
```

## Chunking Experiment

Homework 2 compares different chunking strategies:

| Store | Chunk Size | Overlap |
|---|---:|---:|
| baseline | 500 | 50 |
| lab_small | 200 | 20 |
| lab_large | 800 | 100 |
| lab_no_overlap | 500 | 0 |

Run:

```powershell
python chunk_lab.py
```

The experiment records:

- hits out of 10
- top-1 distance per query
- full comparison table
- winning chunking strategy

The final report is saved in:

```text
chunking_experiment.md
```

## Ignored Files and Folders

The following files and folders are not pushed to GitHub:

```text
.env
data/
chromadb_store/
lab_small/
lab_large/
lab_no_overlap/
.venv/
__pycache__/
```

This keeps API keys, private documents, virtual environments, and local vector stores safe.

## Status

- Homework 1: completed
- Homework 2: chunking experiment completed