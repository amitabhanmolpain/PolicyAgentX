from rag.retriever import get_context

def query_rag(policy_text: str) -> str:
    return get_context(policy_text, k=6)