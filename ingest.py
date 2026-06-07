from pathlib import Path
import shutil

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from config import Config


DATA_DIR = Path("data")
DEFAULT_PERSIST_DIR = Path("chromadb_store")
COLLECTION_NAME = "hayk_ai_agent"


def load_documents(data_dir: Path = DATA_DIR):
    """
    Load all supported files from the data directory.

    Supported file types:
    - .txt
    - .md
    - .pdf
    """

    if not data_dir.exists():
        raise FileNotFoundError(f"Data folder does not exist: {data_dir}")

    documents = []

    for file_path in data_dir.rglob("*"):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents.extend(loader.load())

        elif suffix == ".md":
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents.extend(loader.load())

        elif suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
            documents.extend(loader.load())

        else:
            print(f"Skipping unsupported file: {file_path}")

    if not documents:
        raise ValueError("No supported documents found in data/ folder.")

    return documents


def build_store(splitter, persist_dir: str | Path = DEFAULT_PERSIST_DIR):
    """
    Build a ChromaDB vector store from documents.

    This function:
    1. loads documents from data/;
    2. splits them into chunks using the provided splitter;
    3. embeds chunks with GoogleGenerativeAIEmbeddings;
    4. stores them in ChromaDB.

    To avoid duplicate chunks on re-run, the old store folder is deleted first.
    """

    Config()

    persist_dir = Path(persist_dir)

    documents = load_documents(DATA_DIR)

    print(f"Loaded documents: {len(documents)}")

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("Chunk count is 0. Something went wrong during splitting.")

    print(f"Chunk count: {len(chunks)}")

    if persist_dir.exists():
        print(f"Removing existing store: {persist_dir}")
        shutil.rmtree(persist_dir)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview"
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(persist_dir)
    )

    print(f"ChromaDB store created successfully: {persist_dir}")

    return len(chunks)


def main():
    """
    Default ingest command.

    Running:
        python ingest.py

    builds the original Homework 1 store:
        chunk_size=500
        chunk_overlap=50
        persist_dir=chromadb_store/
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    build_store(
        splitter=splitter,
        persist_dir=DEFAULT_PERSIST_DIR
    )


if __name__ == "__main__":
    main()