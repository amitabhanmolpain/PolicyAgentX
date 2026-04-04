from pathlib import Path
import argparse

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


DEFAULT_QUERY = "job reservation Karnataka protest"


def ingest_pdfs(pdf_dir: Path, persist_dir: Path, chunk_size: int, chunk_overlap: int) -> Chroma:
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    persist_dir.mkdir(parents=True, exist_ok=True)

    loader = PyPDFDirectoryLoader(str(pdf_dir))
    documents = loader.load()
    print(f"Loaded {len(documents)} pages")

    if not documents:
        raise ValueError(f"No PDF pages loaded from: {pdf_dir}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectordb = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=str(persist_dir),
    )
    print(f"All PDFs embedded into ChromaDB at: {persist_dir}")

    return vectordb


def test_retrieval(vectordb: Chroma, query: str, k: int) -> None:
    print("\nQuick test query:", query)
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    results = retriever.invoke(query)

    if not results:
        print("No results found.")
        return

    for i, doc in enumerate(results, start=1):
        print(f"\nResult {i}")
        print(doc.page_content)
        print("---")


def parse_args() -> argparse.Namespace:
    backend_dir = Path(__file__).resolve().parents[2]
    default_pdf_dir = backend_dir / "rag" / "ingest" / "protests"
    default_persist_dir = backend_dir / "chroma_db" / "protests"

    parser = argparse.ArgumentParser(description="Ingest protest PDFs into ChromaDB and test retrieval.")
    parser.add_argument("--pdf-dir", type=Path, default=default_pdf_dir, help="Directory containing PDFs")
    parser.add_argument("--persist-dir", type=Path, default=default_persist_dir, help="Chroma persistence directory")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--query", type=str, default=DEFAULT_QUERY, help="Test query")
    parser.add_argument("--k", type=int, default=3, help="Number of retrieval results")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vectordb = ingest_pdfs(
        pdf_dir=args.pdf_dir,
        persist_dir=args.persist_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    test_retrieval(vectordb=vectordb, query=args.query, k=args.k)


if __name__ == "__main__":
    main()
