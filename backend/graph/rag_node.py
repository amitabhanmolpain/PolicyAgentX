from rag.retriever import get_context

def rag_node(state):
    context = get_context(state["policy"])
    return {"context": context}  # passes to next node