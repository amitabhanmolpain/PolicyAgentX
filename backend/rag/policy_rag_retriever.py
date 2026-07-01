from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import numpy as np
from chromadb import PersistentClient
from langchain_community.vectorstores import Chroma
from sklearn.feature_extraction.text import HashingVectorizer


class HashingEmbeddings:
    def __init__(self, n_features: int = 384):
        self.vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm=None,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.vectorizer.transform(texts).toarray().astype(np.float32).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.vectorizer.transform([text]).toarray().astype(np.float32)[0].tolist()


@dataclass
class PolicyRAGRetriever:
    persist_dir: str = "./chroma_db/protests"
    collection_name: str = "langchain"

    def __post_init__(self) -> None:
        self.embedding_function = HashingEmbeddings()

    def _get_vectorstore(self) -> Chroma:
        os.makedirs(self.persist_dir, exist_ok=True)
        return Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_dir,
            embedding_function=self.embedding_function,
        )

    def _search(self, query: str, k: int = 4) -> List[str]:
        try:
            vectorstore = self._get_vectorstore()
            docs = vectorstore.similarity_search(query, k=k)
            return [doc.page_content.strip() for doc in docs if doc.page_content.strip()]
        except Exception:
            return []

    def _format_results(self, query: str, results: List[str], header: str) -> str:
        if not results:
            return f"{header}: No indexed context found for {query}."

        lines = [f"{header}:"]
        for idx, text in enumerate(results, start=1):
            lines.append(f"- {text[:350]}")
        return "\n".join(lines)

    def retrieve_historical_precedents(self, policy_type: str, k: int = 4) -> str:
        results = self._search(f"historical protest precedents for {policy_type}", k=k)
        return self._format_results(policy_type, results, "Historical precedents")

    def retrieve_financial_context(self, policy_topic: str, k: int = 2) -> str:
        results = self._search(f"financial impact and budget context for {policy_topic}", k=k)
        return self._format_results(policy_topic, results, "Financial context")

    def retrieve_demographic_context(self, income_class: str, policy_topic: str, k: int = 2) -> str:
        query = f"demographic impact on {income_class} groups for {policy_topic}"
        results = self._search(query, k=k)
        return self._format_results(policy_topic, results, "Demographic context")