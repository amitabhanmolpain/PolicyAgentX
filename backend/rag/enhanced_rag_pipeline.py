"""
Enhanced RAG Pipeline for Indian Policy Analysis
==================================================
Ingests government data with:
- Financial impact tracking (revenue/loss)
- Demographic segmentation (income classes)
- Historical policy comparisons
- Future impact predictions
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PERSIST_DIR = "./chroma_policy_db_enhanced"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Optimized chunking for policy documents
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MIN_CHUNK_SIZE = 100

# Government data sources with metadata
GOVERNMENT_DATA_SOURCES = {
    "budget": {
        "name": "Union Budget Documents",
        "sources": [
            "https://indiabudget.gov.in/doc/",
        ],
        "metadata": {"category": "budget", "authority": "Finance Ministry"}
    },
    "economic_survey": {
        "name": "Economic Survey",
        "sources": [
            "https://indiabudget.gov.in/economicsurvey/",
        ],
        "metadata": {"category": "economic_data", "authority": "Finance Ministry"}
    },
    "labor_stats": {
        "name": "Labour Force Participation",
        "sources": [
            {
                "name": "PLFS Data",
                "url": "https://mospi.gov.in/plfs",
                "metadata": {"type": "employment", "frequency": "annual"}
            }
        ],
        "metadata": {"category": "labor_market", "authority": "MoSPI"}
    },
    "income_distribution": {
        "name": "Income Distribution Data",
        "sources": [
            {
                "name": "NSS Income Data",
                "url": "https://mospi.gov.in/",
                "metadata": {"type": "income", "demographic_scope": "all_classes"}
            }
        ],
        "metadata": {"category": "demographic_income", "authority": "MoSPI"}
    },
    "historical_policies": {
        "name": "Historical Policy Outcomes",
        "sources": [
            {
                "name": "Policy Implementation Reports",
                "url": "https://pib.gov.in/",
                "metadata": {"type": "implementation", "scope": "historical"}
            }
        ],
        "metadata": {"category": "policy_history", "authority": "PIB"}
    },
}

# ─────────────────────────────────────────────
# 1. METADATA-ENRICHED DOCUMENT CREATION
# ─────────────────────────────────────────────

class MetadataEnrichedDocument:
    """Create documents with financial and demographic metadata"""
    
    @staticmethod
    def create_budget_document(text: str, year: int, amount: float = None) -> Document:
        """Budget-specific metadata"""
        return Document(
            page_content=text,
            metadata={
                "source": "union_budget",
                "year": year,
                "amount_usd_billions": amount,
                "document_type": "budget",
                "indexed_at": datetime.now().isoformat(),
                "retrieval_category": "financial"
            }
        )
    
    @staticmethod
    def create_demographic_document(text: str, income_class: str, 
                                   state: str = None, affected_population: int = None) -> Document:
        """Demographic-aware metadata"""
        return Document(
            page_content=text,
            metadata={
                "source": "demographic_data",
                "income_class": income_class,  # "upper", "middle", "lower_middle", "bpl"
                "state": state,
                "affected_population": affected_population,
                "document_type": "demographic",
                "retrieval_category": "demographic_impact"
            }
        )
    
    @staticmethod
    def create_historical_policy_document(text: str, policy_name: str,
                                         implementation_year: int,
                                         revenue_impact: float = None,
                                         population_affected: int = None) -> Document:
        """Historical policy comparison metadata"""
        return Document(
            page_content=text,
            metadata={
                "source": "historical_policy",
                "policy_name": policy_name,
                "implementation_year": implementation_year,
                "revenue_impact_crores": revenue_impact,
                "population_affected": population_affected,
                "document_type": "historical_outcome",
                "retrieval_category": "precedent_analysis"
            }
        )
    
    @staticmethod
    def create_economic_indicator_document(text: str, indicator_name: str,
                                          time_period: str,
                                          impact_type: str = "economic") -> Document:
        """Economic data with time-series metadata"""
        return Document(
            page_content=text,
            metadata={
                "source": "economic_survey",
                "indicator": indicator_name,
                "time_period": time_period,
                "impact_type": impact_type,  # "gdp", "inflation", "employment", "fiscal"
                "document_type": "economic_indicator",
                "retrieval_category": "economic_baseline"
            }
        )


# ─────────────────────────────────────────────
# 2. INTELLIGENT CHUNKING WITH SEMANTIC GROUPING
# ─────────────────────────────────────────────

class SemanticChunker:
    """Chunk documents while preserving semantic meaning"""
    
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=[
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                " ",
            ],
            length_function=len,
        )
    
    def chunk_with_context(self, documents: List[Document]) -> List[Document]:
        """Chunk while preserving document context"""
        chunked_docs = []
        
        for doc in documents:
            chunks = self.splitter.split_text(doc.page_content)
            
            for i, chunk in enumerate(chunks):
                if len(chunk) >= MIN_CHUNK_SIZE:
                    # Preserve original metadata and add chunk index
                    chunk_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "chunk_size": len(chunk)
                        }
                    )
                    chunked_docs.append(chunk_doc)
        
        return chunked_docs


# ─────────────────────────────────────────────
# 3. GOVERNMENT DATA INGESTION
# ─────────────────────────────────────────────

class GovernmentDataIngester:
    """Ingest data from Indian government sources"""
    
    @staticmethod
    def create_sample_budget_data() -> List[Document]:
        """Create sample budget documents for testing"""
        docs = []
        
        budget_data = {
            "Direct Taxes": "Income tax collection: ₹13.5 lakh crores. Expected increase of 12% YoY",
            "GST Revenue": "Goods and Service Tax: ₹1.8 lakh crores. Stable for middle class",
            "Social Welfare": "MGNREGA budget: ₹73,000 crores. Targets rural lower-income class",
            "Education": "Education budget: ₹1.12 lakh crores. Direct benefit to all economic classes",
            "Healthcare": "Healthcare spending: ₹82,000 crores. AYUSH and PMJAY focus on lower-middle class",
        }
        
        for title, content in budget_data.items():
            doc = MetadataEnrichedDocument.create_budget_document(
                f"{title}\n{content}",
                year=2024,
                amount=float(''.join(filter(str.isdigit, content.split(':')[1].split()[0]))) / 100
            )
            docs.append(doc)
        
        return docs
    
    @staticmethod
    def create_sample_demographic_data() -> List[Document]:
        """Create demographic segmentation data"""
        docs = []
        
        income_classes = {
            "upper": {
                "income_range": "₹50+ lakhs annually",
                "population": "5% of India",
                "characteristics": "Urban, education-focused, capital gains primary income"
            },
            "middle": {
                "income_range": "₹15-50 lakhs annually",
                "population": "15-20% of India",
                "characteristics": "Urban-semi-urban, service sector, salary income"
            },
            "lower_middle": {
                "income_range": "₹5-15 lakhs annually",
                "population": "25-30% of India",
                "characteristics": "Mixed rural-urban, small business, wage earners"
            },
            "bpl": {
                "income_range": "Below ₹5 lakhs annually",
                "population": "45-50% of India",
                "characteristics": "Mostly rural, agriculture/labor dependent"
            }
        }
        
        for class_name, data in income_classes.items():
            content = f"""
Income Class: {class_name.replace('_', ' ').upper()}
Income Range: {data['income_range']}
Population Share: {data['population']}
Characteristics: {data['characteristics']}

Impact Analysis Required:
- Tax impact on this class
- Employment opportunity benefit
- Cost of living impact
- Savings capacity changes
- Access to services impact
            """
            doc = MetadataEnrichedDocument.create_demographic_document(
                content,
                income_class=class_name,
                affected_population=None
            )
            docs.append(doc)
        
        return docs
    
    @staticmethod
    def create_sample_historical_policies() -> List[Document]:
        """Historical policy outcomes for comparison"""
        docs = []
        
        historical_policies = [
            {
                "name": "GST Implementation",
                "year": 2017,
                "revenue": 30000,
                "affected": 150000000,
                "outcome": "Increased tax base by 30%, benefited organized sector, compliance burden on small traders"
            },
            {
                "name": "MGNREGA Enhancement",
                "year": 2019,
                "revenue": -45000,
                "affected": 200000000,
                "outcome": "Provided rural employment, wage increase benefited lower income class, fiscal impact managed"
            },
            {
                "name": "Make in India",
                "year": 2014,
                "revenue": 50000,
                "affected": 100000000,
                "outcome": "Manufacturing jobs created, benefited upper-middle class, impact on traditional sectors mixed"
            }
        ]
        
        for policy in historical_policies:
            content = f"""
Policy: {policy['name']} (Implemented {policy['year']})
Population Affected: {policy['affected']:,}
Revenue Impact: ₹{policy['revenue']:,} crores
Outcome: {policy['outcome']}
            """
            doc = MetadataEnrichedDocument.create_historical_policy_document(
                content,
                policy_name=policy['name'],
                implementation_year=policy['year'],
                revenue_impact=policy['revenue'],
                population_affected=policy['affected']
            )
            docs.append(doc)
        
        return docs
    
    @staticmethod
    def create_sample_economic_indicators() -> List[Document]:
        """Economic baseline data"""
        docs = []
        
        indicators = {
            "GDP Growth": "India's GDP growing at 7-8% annually. Tax revenue elasticity 1.3x",
            "Inflation": "CPI at 5-6% range. Impact varies by income class",
            "Unemployment": "Rural: 3.9%, Urban: 7.2%. Regional variations significant",
            "Labor Force": "500M+ in labor force, 60% informal sector",
            "Government Revenue": "Tax-to-GDP ratio 11.5%. Needs optimization",
        }
        
        for indicator, data in indicators.items():
            doc = MetadataEnrichedDocument.create_economic_indicator_document(
                f"{indicator}: {data}",
                indicator_name=indicator,
                time_period="2024"
            )
            docs.append(doc)
        
        return docs


# ─────────────────────────────────────────────
# 4. OPTIMIZED VECTOR STORE WITH FILTERING
# ─────────────────────────────────────────────

class OptimizedVectorStore:
    """ChromaDB with metadata filtering for efficient retrieval"""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.persist_dir = PERSIST_DIR
    
    def create_store(self, documents: List[Document]) -> Chroma:
        """Create ChromaDB with metadata indexing"""
        return Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name="policy_analysis"
        )
    
    def retrieve_by_retrieval_category(self, vectorstore: Chroma, 
                                      query: str, 
                                      category: str,
                                      k: int = 5) -> List[Document]:
        """Retrieve documents filtered by category"""
        # Metadata filtering for efficiency
        results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"retrieval_category": category}
        )
        return results
    
    def retrieve_by_income_class(self, vectorstore: Chroma,
                                query: str,
                                income_class: str,
                                k: int = 3) -> List[Document]:
        """Retrieve demographic-specific documents"""
        results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"income_class": income_class}
        )
        return results
    
    def retrieve_by_time_period(self, vectorstore: Chroma,
                               query: str,
                               start_year: int,
                               end_year: int,
                               k: int = 5) -> List[Document]:
        """Retrieve historical policies in time range"""
        # This requires custom filtering logic
        results = vectorstore.similarity_search(query, k=k)
        filtered = [
            doc for doc in results 
            if "implementation_year" in doc.metadata 
            and start_year <= doc.metadata.get("implementation_year", 0) <= end_year
        ]
        return filtered[:k]


# ─────────────────────────────────────────────
# 5. MAIN PIPELINE ORCHESTRATION
# ─────────────────────────────────────────────

def build_enhanced_rag_pipeline():
    """Build complete RAG pipeline with all data sources"""
    
    print("\n" + "="*70)
    print("  ENHANCED RAG PIPELINE FOR POLICY ANALYSIS")
    print("="*70)
    
    # Collect all documents
    all_documents = []
    
    print("\n📊 Ingesting Government Data Sources...")
    
    # 1. Budget data
    print("  → Union Budget documents...")
    all_documents.extend(GovernmentDataIngester.create_sample_budget_data())
    
    # 2. Demographic data
    print("  → Income class demographic data...")
    all_documents.extend(GovernmentDataIngester.create_sample_demographic_data())
    
    # 3. Historical policies
    print("  → Historical policy outcomes...")
    all_documents.extend(GovernmentDataIngester.create_sample_historical_policies())
    
    # 4. Economic indicators
    print("  → Economic indicators baseline...")
    all_documents.extend(GovernmentDataIngester.create_sample_economic_indicators())
    
    print(f"\n✓ Total documents ingested: {len(all_documents)}")
    
    # Chunk with semantic grouping
    print("\n✂️  Chunking with semantic grouping...")
    chunker = SemanticChunker()
    chunked_docs = chunker.chunk_with_context(all_documents)
    print(f"  → {len(chunked_docs)} semantic chunks created")
    
    # Create optimized vector store
    print("\n🔄 Building ChromaDB with metadata indexing...")
    vectorstore = OptimizedVectorStore()
    db = vectorstore.create_store(chunked_docs)
    
    print(f"✅ Enhanced RAG pipeline ready!")
    print(f"   Location: {vectorstore.persist_dir}")
    print(f"   Total indexed documents: {len(chunked_docs)}")
    print(f"   Embedding model: {EMBEDDING_MODEL}")
    
    return db, vectorstore


# ─────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    db, vectorstore = build_enhanced_rag_pipeline()
    
    # Example queries
    print("\n" + "="*70)
    print("  EXAMPLE QUERIES")
    print("="*70)
    
    print("\n1️⃣  Query: Impact on Lower-Middle Class")
    results = vectorstore.retrieve_by_income_class(db, "tax increase impact", "lower_middle", k=3)
    for doc in results:
        print(f"   - {doc.page_content[:100]}...")
    
    print("\n2️⃣  Query: Historical Policy Comparison")
    results = vectorstore.retrieve_by_time_period(db, "policy implementation", 2014, 2020, k=3)
    for doc in results:
        print(f"   - {doc.page_content[:100]}...")
    
    print("\n3️⃣  Query: Financial Impact Analysis")
    results = vectorstore.retrieve_by_retrieval_category(db, "revenue impact", "financial", k=3)
    for doc in results:
        print(f"   - {doc.page_content[:100]}...")
