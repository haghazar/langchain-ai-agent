from pathlib import Path

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import Config


PERSIST_DIR = Path("chromadb_store")
COLLECTION_NAME = "hayk_ai_agent"


def format_documents(documents):
    """
    Convert retrieved documents into a single context string.
    """

    if not documents:
        return ""

    formatted_chunks = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown source")
        page = document.metadata.get("page", None)

        metadata_text = f"Source: {source}"
        if page is not None:
            metadata_text += f", Page: {page}"

        formatted_chunks.append(
            f"[Chunk {index}]\n"
            f"{metadata_text}\n"
            f"{document.page_content}"
        )

    return "\n\n".join(formatted_chunks)


def create_retriever():
    """
    Load the existing ChromaDB store and create a retriever.
    """

    if not PERSIST_DIR.exists():
        raise FileNotFoundError(
            "chromadb_store/ folder was not found. Run python ingest.py first."
        )

    Config()

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview"
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings
    )

    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 4
        }
    )

    return retriever


def create_rag_chain():
    """
    Create a RAG chain using LCEL.

    The chain:
    1. retrieves relevant context from ChromaDB;
    2. inserts context and question into the prompt;
    3. sends the prompt to Gemini;
    4. returns a plain string answer.
    """

    retriever = create_retriever()

    prompt = ChatPromptTemplate.from_template(
        """
You are a careful RAG assistant.

Use ONLY the context below to answer the question.

If the answer is not clearly present in the context, answer exactly:
"I don't have information about that."

Do not use your general knowledge.
Do not guess.
Do not add information that is not in the context.

Context:
{context}

Question:
{question}

Answer:
"""
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    chain = (
        {
            "context": retriever | format_documents,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def ask_question(chain, question):
    """
    Ask one question and print the answer.
    """

    print("=" * 80)
    print(f"Question: {question}")
    print("-" * 80)

    answer = chain.invoke(question)

    print(f"Answer: {answer}")
    print("=" * 80)
    print()

    return answer


def main():
    chain = create_rag_chain()

    questions = [
        "How is an asset tracked in public chaincode state?",
        "Who must endorse the asset transfer request?",
        "What does the chaincode verify before transferring the asset?",
        "When was the Eiffel Tower built?"
    ]

    for question in questions:
        ask_question(chain, question)


if __name__ == "__main__":
    main()