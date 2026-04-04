"""
Efficient RAG Retriever for Policy Analysis
============================================
Retrieves relevant government data to provide context for policy prediction
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


class PolicyRAGRetriever:
    """Efficient retrieval of government data for policy analysis"""
    
    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.vectorstore = None
        self._load_vectorstore()

    def _candidate_persist_dirs(self) -> List[Path]:
        """Return ordered candidate ChromaDB directories."""
        backend_dir = Path(__file__).resolve().parents[1]

        user_input = [Path(self.persist_dir)] if self.persist_dir else []
        env_dir = os.getenv("POLICY_RAG_DB_DIR")
        env_input = [Path(env_dir)] if env_dir else []

        defaults = [
            backend_dir / "chroma_db" / "protests",
            backend_dir / "chroma_policy_db_enhanced",
            backend_dir / "chroma_policy_db",
        ]

        ordered = user_input + env_input + defaults
        unique = []
        seen = set()
        for path in ordered:
            key = str(path.resolve()) if path.exists() else str(path)
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    def _candidate_collections(self) -> List[str]:
        """Return ordered candidate Chroma collection names."""
        env_collection = os.getenv("POLICY_RAG_COLLECTION")
        candidates = [self.collection_name, env_collection, "langchain", "policy_analysis"]
        return [name for name in candidates if name]
    
    def _load_vectorstore(self):
        """Load existing vector store with automatic fallback discovery."""
        best_store = None
        best_count = -1
        best_dir = None
        best_collection = None

        for persist_path in self._candidate_persist_dirs():
            if not persist_path.exists():
                continue

            for collection in self._candidate_collections():
                try:
                    candidate = Chroma(
                        persist_directory=str(persist_path),
                        embedding_function=self.embeddings,
                        collection_name=collection,
                    )

                    # Prefer the first non-empty collection.
                    try:
                        count = candidate._collection.count()
                    except Exception:
                        count = 0

                    if count > best_count:
                        best_store = candidate
                        best_count = count
                        best_dir = str(persist_path)
                        best_collection = collection
                except Exception:
                    continue

        if best_store is not None:
            self.vectorstore = best_store
            self.persist_dir = best_dir
            self.collection_name = best_collection
            print(
                f"✅ Loaded vector store from {self.persist_dir} "
                f"(collection={self.collection_name}, docs={best_count})"
            )
            return

        print("⚠️  Could not find an existing populated ChromaDB collection.")
        print("   Run ingestion first, e.g. python rag/ingest/ingest_protests_pdfs.py")
        self.vectorstore = None

    def _similarity_search(self, query: str, k: int) -> List[Document]:
        """Shared safe similarity search helper."""
        if not self.vectorstore:
            return []
        try:
            return self.vectorstore.similarity_search(query, k=k)
        except Exception as e:
            print(f"⚠️  similarity_search failed: {e}")
            return []
    
    def retrieve_financial_context(self, policy_topic: str, k: int = 5) -> str:
        """Get historical financial data for similar policies"""
        if not self.vectorstore:
            return ""
        
        query = f"Financial impact revenue loss budget {policy_topic}"
        docs = self._similarity_search(query, k)
        
        context = "FINANCIAL CONTEXT:\n"
        category_docs = [d for d in docs if d.metadata.get("retrieval_category") == "financial"]
        if not category_docs:
            category_docs = docs
        for doc in category_docs:
            context += f"- {doc.page_content[:200]}\n"
        
        return context
    
    def retrieve_demographic_context(self, income_class: str, 
                                    policy_topic: str, k: int = 5) -> str:
        """Get demographic data for income class impact analysis"""
        if not self.vectorstore:
            return ""
        
        query = f"{income_class} income class impact {policy_topic}"
        docs = self._similarity_search(query, k)
        
        context = f"DEMOGRAPHIC CONTEXT ({income_class.upper()}):\n"
        category_docs = [d for d in docs if d.metadata.get("retrieval_category") == "demographic_impact"]
        if not category_docs:
            category_docs = docs

        for doc in category_docs:
            context += f"- Population {doc.metadata.get('affected_population', 'N/A')}\n"
            context += f"  {doc.page_content[:150]}\n"
        
        return context
    
    def retrieve_historical_precedents(self, policy_type: str, k: int = 3) -> str:
        """Get similar historical policies for comparison"""
        if not self.vectorstore:
            return ""
        
        query = f"historical policy {policy_type} implementation outcomes"
        docs = self._similarity_search(query, k)
        
        context = "HISTORICAL PRECEDENTS:\n"
        history_docs = [d for d in docs if d.metadata.get("document_type") == "historical_outcome"]
        if not history_docs:
            history_docs = docs

        for doc in history_docs:
            year = doc.metadata.get("implementation_year", "?")
            revenue = doc.metadata.get("revenue_impact_crores", "?")
            context += f"- {doc.metadata.get('policy_name', 'Policy')} ({year}): "
            context += f"₹{revenue}Cr impact\n"
            context += f"  {doc.page_content[:150]}\n"
        
        return context
    
    def retrieve_economic_baseline(self, k: int = 3) -> str:
        """Get current economic indicators for baseline"""
        if not self.vectorstore:
            return ""
        
        docs = self._similarity_search("GDP inflation unemployment growth", k)
        
        context = "ECONOMIC BASELINE:\n"
        baseline_docs = [d for d in docs if d.metadata.get("retrieval_category") == "economic_baseline"]
        if not baseline_docs:
            baseline_docs = docs

        for doc in baseline_docs:
            context += f"- {doc.page_content[:200]}\n"
        
        return context
    
    def get_comprehensive_context(self, policy_text: str, 
                                 policy_type: str = "fiscal") -> str:
        """Get all relevant context for comprehensive analysis"""
        
        context = f"""
POLICY ANALYSIS CONTEXT
{'='*50}

"""
        
        # Economic baseline
        context += self.retrieve_economic_baseline(k=2)
        context += "\n"
        
        # Financial context
        context += self.retrieve_financial_context(policy_type, k=3)
        context += "\n"
        
        # Demographic contexts for each class
        for income_class in ["upper", "middle", "lower_middle", "bpl"]:
            context += self.retrieve_demographic_context(income_class, policy_type, k=2)
            context += "\n"
        
        # Historical precedents
        context += self.retrieve_historical_precedents(policy_type, k=2)
        
        return context
    
    def enhance_policy_with_context(self, policy_text: str) -> str:
        """Enhance policy with retrieved context for better analysis"""
        
        # Extract policy type from text
        policy_lower = policy_text.lower()
        if "tax" in policy_lower or "revenue" in policy_lower:
            policy_type = "taxation"
        elif "subsidy" in policy_lower or "welfare" in policy_lower:
            policy_type = "welfare"
        elif "employment" in policy_lower or "job" in policy_lower:
            policy_type = "employment"
        elif "education" in policy_lower:
            policy_type = "education"
        elif "health" in policy_lower:
            policy_type = "healthcare"
        else:
            policy_type = "general"
        
        context = self.get_comprehensive_context(policy_text, policy_type)
        
        return f"""
POLICY TO ANALYZE:
{policy_text}

{context}

ANALYSIS INSTRUCTIONS:
1. Consider all demographic impacts above
2. Compare with historical precedents
3. Account for current economic baseline
4. Provide specific financial estimates
5. Quantify impact by income class
"""


# ─────────────────────────────────────────────
# INTEGRATION WITH POLICY PREDICTOR
# ─────────────────────────────────────────────

def analyze_policy_with_rag(policy_text: str) -> Dict[str, Any]:
    """Complete pipeline: RAG + Prediction"""
    
    from agents.policy_predictor import PolicyPredictionEngine, PolicyAnalysisReporter
    
    print("🔄 Starting RAG-enhanced policy analysis...\n")
    
    # Step 1: Retrieve context
    print("Step 1️⃣ : Retrieving contextual data from government sources...")
    retriever = PolicyRAGRetriever()
    enhanced_policy = retriever.enhance_policy_with_context(policy_text)
    
    # Step 2: Analyze with context
    print("Step 2️⃣ : Analyzing policy with Vertex AI prediction engine...")
    predictor = PolicyPredictionEngine()
    analysis = predictor.comprehensive_policy_analysis(
        policy_text, 
        historical_context=enhanced_policy
    )
    
    # Step 3: Generate report
    print("Step 3️⃣ : Generating comprehensive report...\n")
    report = PolicyAnalysisReporter.format_policy_summary(analysis)
    
    return {
        "policy": policy_text,
        "analysis": analysis,
        "report": report,
        "context_sources": enhanced_policy
    }


if __name__ == "__main__":
    # Example usage
    sample_policy = """
    Proposed: Increase GST on luxury goods from 18% to 28%
    Expected to generate additional ₹20,000 crores in tax revenue
    Targets high-income consumers
    """
    
    result = analyze_policy_with_rag(sample_policy)
    print(result["report"])
