from __future__ import annotations

import traceback

from app.services.rag_service import get_rag_service


def handle_chat(data):
    if not data:
        return {"error": "Request body is required"}, 400

    question = data.get("question") or data.get("text")
    top_k = data.get("top_k", 4)

    if not question:
        return {"error": "Question is required"}, 400

    try:
        result = get_rag_service().answer_question(question=question, top_k=int(top_k))
        return result, 200
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except Exception as exc:
        return {"error": f"Chat failed: {str(exc)}", "details": traceback.format_exc()}, 500
