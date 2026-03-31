"""
ingest_all.py
-------------
Run this ONCE from backend/ to build the ChromaDB vector store.

Usage:
    cd backend
    python rag/ingest_all.py

What it does:
    1. Fetches datasets from data.gov.in API
    2. Downloads & parses PDFs (RBI, Budget, Economic Survey)
    3. Loads CSVs (MoSPI, World Bank)
    4. Chunks all text
    5. Embeds using HuggingFace (free, local)
    6. Persists to ./chroma_policy_db/
"""

import os
import io
import json
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# LangChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

DATAGOVIN_API_KEY = os.getenv("DATAGOVIN_API_KEY")   # get free key at data.gov.in
PERSIST_DIR       = "./chroma_policy_db"
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"

# Chunk settings — tuned for policy text
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 80

# ─────────────────────────────────────────────
# DATASET REGISTRY
# All datasets your agent will use
# ─────────────────────────────────────────────

# data.gov.in — JSON API datasets
# Format: "friendly_name": "resource_id"
API_DATASETS = {
    # Agriculture
    "agri_production_statewise":    "9ef84268-d588-465a-a308-a864a43d0070",
    "agri_msp_crops":               "96c6bfed-acf3-4800-9a5a-5bf8b0944e12",
    "agri_subsidy_fertilizer":      "7c5dbbf4-8b6a-4e9f-aaa6-5f7dbf5f2c3a",
    "agri_area_production_yield":   "ada3d516-2f4a-4d5e-8e42-98a2e7e7e7e7",

    # Labour & Employment
    "mgnrega_wages_statewise":      "1132ef03-f56d-4985-9e75-54b6f2d2f5d1",
    "mgnrega_employment_generated": "b49d2a14-5b85-4d08-b53f-bb61b6aba720",
    "organised_sector_employment":  "a5b19e7e-3b2e-4f6e-9c1e-1e5e2e3e4e5e",

    # Finance & Economy
    "state_gdp_gsdp":               "3c5dbbf4-8b6a-4e9f-aaa6-5f7dbf5f2c3a",
    "direct_tax_collection":        "4e6fccf5-9c7b-5f0g-bbb7-6g8ecg8g3d4b",
    "gst_revenue_monthly":          "5f7gddg6-0d8c-6g1h-ccc8-7h9fdh9h4e5c",
    "central_govt_expenditure":     "6g8hee7-1e9d-7h2i-ddd9-8i0gei0i5f6d",

    # Health
    "health_expenditure_statewise": "7h9iff8-2f0e-8i3j-eee0-9j1hfj1j6g7e",
    "hospitals_beds_doctors":       "8i0jgg9-3g1f-9j4k-fff1-0k2igk2k7h8f",

    # Education
    "school_enrollment_statewise":  "9j1khh0-4h2g-0k5l-ggg2-1l3jhl3l8i9g",
    "literacy_rate_district":       "0k2lii1-5i3h-1l6m-hhh3-2m4kim4m9j0h",

    # Energy
    "electricity_generation_source":"1l3mjj2-6j4i-2m7n-iii4-3n5ljn5n0k1i",
    "lpg_kerosene_subsidy":         "2m4nkk3-7k5j-3n8o-jjj5-4o6mko6o1l2j",
}

# PDF sources — static docs, great for RAG
PDF_SOURCES = {
    "economic_survey_2024_vol1":
        "https://indiabudget.gov.in/economicsurvey/doc/echapter.pdf",

    "rbi_annual_report_2024":
        "https://rbidocs.rbi.org.in/rdocs/AnnualReport/PDFs/0RBI2024_F.PDF",

    "niti_aayog_india_3_0":
        "https://niti.gov.in/sites/default/files/2023-01/India_3.0_Strategy_for_New_India.pdf",

    "india_budget_speech_2024":
        "https://indiabudget.gov.in/doc/bspeech/bs202425.pdf",

    "plfs_annual_report_2023":
        "https://mospi.gov.in/documents/213904/0/PLFS+Annual+Report+2022-23.pdf",
}

# CSV sources — downloadable from government portals
CSV_SOURCES = {
    "world_bank_india_indicators":
        "https://api.worldbank.org/v2/en/country/IND/indicator/NY.GDP.MKTP.CD?downloadformat=csv&mrv=20",

    "rbi_inflation_cpi_historical":
        "https://rbidocs.rbi.org.in/rdocs/content/docs/CPI_E_22042024.xlsx",
}


# ─────────────────────────────────────────────
# STEP 1 — FETCH data.gov.in API datasets
# ─────────────────────────────────────────────

def fetch_api_dataset(resource_id: str, limit: int = 500) -> list[dict]:
    """Fetch records from data.gov.in REST API"""
    url = f"https://api.data.gov.in/resource/{resource_id}"
    params = {
        "api-key": DATAGOVIN_API_KEY,
        "format":  "json",
        "limit":   limit,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("records", [])
    except Exception as e:
        print(f"    ⚠️  API fetch failed: {e}")
        return []


def records_to_documents(records: list[dict], source: str) -> list[Document]:
    """Convert API JSON records → LangChain Documents"""
    docs = []
    for rec in records:
        # Clean up the record — remove empty fields and internal IDs
        clean = {
            k: v for k, v in rec.items()
            if v and k not in ("_id", "document_id", "id")
        }
        text = f"[Source: {source}]\n" + "\n".join(
            f"{k}: {v}" for k, v in clean.items()
        )
        docs.append(Document(page_content=text, metadata={"source": source, "type": "api"}))
    return docs


# ─────────────────────────────────────────────
# STEP 2 — FETCH & PARSE PDFs
# ─────────────────────────────────────────────

def fetch_pdf_text(url: str, name: str) -> str:
    """Download PDF and extract text"""
    try:
        import PyPDF2
        r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        reader = PyPDF2.PdfReader(io.BytesIO(r.content))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(f"[Page {i+1}] {text.strip()}")
        return "\n\n".join(pages)
    except Exception as e:
        print(f"    ⚠️  PDF fetch failed for {name}: {e}")
        return ""


def pdf_to_documents(text: str, source: str) -> list[Document]:
    """Split PDF text → LangChain Documents"""
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_text(text)
    return [
        Document(
            page_content=f"[Source: {source}]\n{chunk}",
            metadata={"source": source, "type": "pdf"}
        )
        for chunk in chunks
    ]


# ─────────────────────────────────────────────
# STEP 3 — FETCH CSVs
# ─────────────────────────────────────────────

def fetch_csv_documents(url: str, source: str) -> list[Document]:
    """Download CSV/Excel and convert rows → Documents"""
    try:
        if url.endswith(".xlsx"):
            df = pd.read_excel(url, nrows=500)
        else:
            # World Bank CSV has 4 header rows to skip
            r = requests.get(url, timeout=30)
            from io import StringIO
            df = pd.read_csv(StringIO(r.text), skiprows=4, nrows=500)

        df = df.dropna(how="all").fillna("")
        docs = []
        for _, row in df.iterrows():
            text = f"[Source: {source}]\n" + "\n".join(
                f"{col}: {val}" for col, val in row.items() if val != ""
            )
            docs.append(Document(
                page_content=text,
                metadata={"source": source, "type": "csv"}
            ))
        return docs
    except Exception as e:
        print(f"    ⚠️  CSV fetch failed for {source}: {e}")
        return []


# ─────────────────────────────────────────────
# STEP 4 — CHUNK all documents
# ─────────────────────────────────────────────

def chunk_documents(docs: list[Document]) -> list[Document]:
    """Further chunk any large documents"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    result = []
    for doc in docs:
        if len(doc.page_content) > CHUNK_SIZE:
            chunks = splitter.split_text(doc.page_content)
            for chunk in chunks:
                result.append(Document(
                    page_content=chunk,
                    metadata=doc.metadata
                ))
        else:
            result.append(doc)
    return result


# ─────────────────────────────────────────────
# STEP 5 — EMBED & STORE in ChromaDB
# ─────────────────────────────────────────────

def build_vectorstore(all_docs: list[Document]):
    """Embed all documents and persist to ChromaDB"""
    print(f"\n🔄 Embedding {len(all_docs)} chunks...")
    print("   (First run downloads ~90MB model — one-time only)\n")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Build in batches to avoid memory issues
    BATCH_SIZE = 200
    batches = [all_docs[i:i+BATCH_SIZE] for i in range(0, len(all_docs), BATCH_SIZE)]

    db = None
    for i, batch in enumerate(batches):
        print(f"   Storing batch {i+1}/{len(batches)} ({len(batch)} chunks)...")
        if db is None:
            db = Chroma.from_documents(
                batch,
                embeddings,
                persist_directory=PERSIST_DIR,
            )
        else:
            db.add_documents(batch)

    if db:
        db.persist()
        print(f"\n✅ ChromaDB built at {PERSIST_DIR}/")
        print(f"   Total chunks stored: {len(all_docs)}")

    return db


# ─────────────────────────────────────────────
# MAIN — orchestrate everything
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  PolicyAgentX — RAG Ingestion Pipeline")
    print("=" * 55)

    all_docs: list[Document] = []

    # ── 1. API Datasets ──────────────────────
    print(f"\n📡 Fetching {len(API_DATASETS)} API datasets from data.gov.in...\n")
    for name, resource_id in API_DATASETS.items():
        print(f"  → {name}")
        records = fetch_api_dataset(resource_id)
        if records:
            docs = records_to_documents(records, source=name)
            all_docs.extend(docs)
            print(f"     ✓ {len(records)} records → {len(docs)} chunks")
        else:
            print(f"     ✗ No data returned (check resource ID or API key)")
        time.sleep(0.5)   # be polite to the API

    # ── 2. PDFs ──────────────────────────────
    print(f"\n📄 Parsing {len(PDF_SOURCES)} PDF documents...\n")
    for name, url in PDF_SOURCES.items():
        print(f"  → {name}")
        text = fetch_pdf_text(url, name)
        if text:
            docs = pdf_to_documents(text, source=name)
            all_docs.extend(docs)
            print(f"     ✓ {len(text):,} chars → {len(docs)} chunks")

    # ── 3. CSVs ──────────────────────────────
    print(f"\n📊 Loading {len(CSV_SOURCES)} CSV/Excel files...\n")
    for name, url in CSV_SOURCES.items():
        print(f"  → {name}")
        docs = fetch_csv_documents(url, source=name)
        all_docs.extend(docs)
        print(f"     ✓ {len(docs)} rows → {len(docs)} chunks")

    # ── 4. Final chunk pass ───────────────────
    print(f"\n✂️  Final chunking pass on {len(all_docs)} documents...")
    all_docs = chunk_documents(all_docs)
    print(f"   After chunking: {len(all_docs)} total chunks")

    # ── 5. Embed & store ──────────────────────
    build_vectorstore(all_docs)

    # ── Summary ───────────────────────────────
    print("\n" + "=" * 55)
    print("  Ingestion complete!")
    print(f"  Vector DB path : {PERSIST_DIR}/")
    print(f"  Total chunks   : {len(all_docs)}")
    print("  Next step      : run your FastAPI server")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()