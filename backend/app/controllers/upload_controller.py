from __future__ import annotations

import traceback

from app.services.rag_service import get_rag_service


def handle_upload(file):
    if not file:
        return {"error": "No file uploaded"}, 400

    try:
        result = get_rag_service().ingest_pdf(file)
        return result, 200
    except ValueError as exc:
        return {"error": str(exc)}, 400
    except Exception as exc:
        return {"error": f"Upload failed: {str(exc)}", "details": traceback.format_exc()}, 500


def handle_reset():
    try:
        result = get_rag_service().reset_vector_store()
        return result, 200
    except Exception as exc:
        return {"error": f"Reset failed: {str(exc)}", "details": traceback.format_exc()}, 500