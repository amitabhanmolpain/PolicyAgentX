from pipeline.embed import load_vectorstore

db = load_vectorstore()

def get_context(query: str, k=6) -> str:
    """Returns top-k relevant chunks for any policy query"""
    docs = db.similarity_search(query, k=k)
    return "\n\n---\n\n".join([
        f"[Source: {d.metadata['source']}]\n{d.page_content}"
        for d in docs
    ])