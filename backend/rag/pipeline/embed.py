from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Free model, runs locally, no API key needed
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def build_vectorstore(docs, persist_dir="./chroma_policy_db"):
    db = Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=persist_dir
    )
    db.persist()
    print(f"✅ Stored {len(docs)} chunks in ChromaDB")
    return db

def load_vectorstore(persist_dir="./chroma_policy_db"):
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )