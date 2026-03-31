from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

PERSIST_DIR = "./chroma_policy_db"  # relative to backend/

def build_vectorstore(docs):
    # This LINE creates the folder automatically ↓
    db = Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=PERSIST_DIR
    )
    db.persist()
    return db

def load_vectorstore():
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )