from __future__ import annotations

from pathlib import Path
from typing import Any, List

import numpy as np

from .data_loader import load_all_documents
from .embedding import EmbeddingPipeline


class RAGPipeline:
    """Lightweight integration wrapper around the existing RAG source modules."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.embedding_pipeline = EmbeddingPipeline(
            model_name=model_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def load_documents(self, data_dir: str | Path) -> List[Any]:
        return load_all_documents(str(data_dir))

    def chunk_documents(self, documents: List[Any]) -> List[Any]:
        return self.embedding_pipeline.chunk_documents(documents)

    def embed_chunks(self, chunks: List[Any]) -> np.ndarray:
        return self.embedding_pipeline.embed_chunks(chunks)

    def embed_query(self, query: str) -> np.ndarray:
        return np.asarray(self.embedding_pipeline.model.encode([query]), dtype=np.float32)[0]