from __future__ import annotations

import logging
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.services.groq_service import generate, is_error_response, response_text
from rag.src.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class RAGService:
    """Owns the Chroma collection, embedding pipeline, and Gemini-backed QA flow."""

    def __init__(
        self,
        data_dir: str,
        persist_dir: str,
        collection_name: str = "policy_rag",
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.persist_dir = Path(persist_dir).resolve()
        self.collection_name = collection_name
        self.lock = threading.RLock()
        self.pipeline = RAGPipeline(
            model_name=model_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        self.upload_dir = self.data_dir / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self._get_collection()
        logger.info("RAG service initialized with collection '%s' at %s", self.collection_name, self.persist_dir)

    def _get_collection(self):
        return self.client.get_or_create_collection(name=self.collection_name)

    def _refresh_collection(self):
        self.collection = self._get_collection()
        return self.collection

    def _build_chunk_metadata(self, source_file: str, chunk_index: int, chunk: Any) -> Dict[str, Any]:
        metadata = dict(getattr(chunk, "metadata", {}) or {})
        metadata.update(
            {
                "source_file": source_file,
                "chunk_index": chunk_index,
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return metadata

    def ingest_pdf(self, file_storage: FileStorage) -> Dict[str, Any]:
        if not file_storage or not getattr(file_storage, "filename", None):
            raise ValueError("No file uploaded")

        if not file_storage.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported")

        safe_name = secure_filename(file_storage.filename)
        upload_id = uuid.uuid4().hex
        upload_path = self.upload_dir / upload_id / safe_name
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        file_storage.save(str(upload_path))

        documents = self.pipeline.load_documents(upload_path.parent)
        if not documents:
            raise ValueError("No readable documents were found in the uploaded file")

        chunks = self.pipeline.chunk_documents(documents)
        if not chunks:
            raise ValueError("The uploaded document did not produce any chunks")

        embeddings = self.pipeline.embed_chunks(chunks)
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [self._build_chunk_metadata(safe_name, idx, chunk) for idx, chunk in enumerate(chunks)]
        ids = [f"{upload_id}_{idx}" for idx in range(len(chunks))]

        with self.lock:
            self.collection = self._refresh_collection()
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings.tolist(),
            )

        return {
            "message": "PDF indexed successfully",
            "filename": safe_name,
            "chunks_indexed": len(chunks),
            "collection": self.collection_name,
            "persist_dir": str(self.persist_dir),
        }

    def answer_question(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("Question is required")

        query_embedding = self.pipeline.embed_query(question)
        with self.lock:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=max(1, top_k),
                include=["documents", "metadatas", "distances"],
            )

        documents = (results or {}).get("documents", [[]])[0] or []
        metadatas = (results or {}).get("metadatas", [[]])[0] or []
        distances = (results or {}).get("distances", [[]])[0] or []
        context = self._build_context(documents, metadatas, distances)

        prompt = self._build_prompt(question, context)
        gemini_response = generate(prompt)
        answer = response_text(gemini_response)

        if is_error_response(gemini_response):
            raise RuntimeError(answer or "Gemini request failed")

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "matches": self._format_matches(documents, metadatas, distances),
            "collection": self.collection_name,
        }

    def reset_vector_store(self) -> Dict[str, Any]:
        with self.lock:
            if self.persist_dir.exists():
                shutil.rmtree(self.persist_dir)
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self._get_collection()

        return {
            "message": "Vector database reset successfully",
            "collection": self.collection_name,
            "persist_dir": str(self.persist_dir),
        }

    def _build_context(self, documents: List[str], metadatas: List[Dict[str, Any]], distances: List[float]) -> str:
        if not documents:
            return "No relevant context found in the vector database."

        lines: List[str] = []
        for idx, document in enumerate(documents, start=1):
            metadata = metadatas[idx - 1] if idx - 1 < len(metadatas) else {}
            source_file = metadata.get("source_file", "unknown")
            distance = distances[idx - 1] if idx - 1 < len(distances) else None
            prefix = f"[{idx}] source={source_file}"
            if distance is not None:
                prefix += f" score={distance:.4f}"
            lines.append(f"{prefix}\n{document.strip()}")
        return "\n\n".join(lines)

    def _format_matches(self, documents: List[str], metadatas: List[Dict[str, Any]], distances: List[float]) -> List[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        for idx, document in enumerate(documents, start=1):
            metadata = metadatas[idx - 1] if idx - 1 < len(metadatas) else {}
            match = {
                "rank": idx,
                "text": document,
                "metadata": metadata,
            }
            if idx - 1 < len(distances):
                match["distance"] = distances[idx - 1]
            matches.append(match)
        return matches

    def _build_prompt(self, question: str, context: str) -> str:
        return (
            "You are a policy research assistant. Answer strictly from the retrieved context. "
            "If the context does not contain the answer, say so clearly and avoid fabricating details.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )


_rag_service: RAGService | None = None


def build_rag_service(data_dir: str, persist_dir: str, collection_name: str = "policy_rag") -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(
            data_dir=data_dir,
            persist_dir=persist_dir,
            collection_name=collection_name,
        )
    return _rag_service


def get_rag_service() -> RAGService:
    from flask import current_app

    service = current_app.extensions.get("rag_service")
    if service is None:
        raise RuntimeError("RAG service has not been initialized")
    return service
