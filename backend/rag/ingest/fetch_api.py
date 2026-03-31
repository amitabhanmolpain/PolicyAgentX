import requests, os

API_KEY = os.getenv("DATAGOVIN_API_KEY")

# All resource IDs you need — copy these exactly
DATASETS = {
    "mgnrega_wages":    "7c5dbbf4-8b6a-4e9f-aaa6-5f7dbf5f2c3a",
    "agri_production":  "9ef84268-d588-465a-a308-a864a43d0070",
    "state_gdp":        "1132ef03-f56d-4985-9e75-54b6f2d2f5d1",
    "food_inflation":   "b49d2a14-5b85-4d08-b53f-bb61b6aba720",
}

def fetch_dataset(resource_id: str, limit=500) -> list[dict]:
    url = f"https://api.data.gov.in/resource/{resource_id}"
    params = {"api-key": API_KEY, "format": "json", "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    return r.json().get("records", [])

def records_to_text(records: list[dict], dataset_name: str) -> list[str]:
    """Convert each row into a readable text chunk"""
    chunks = []
    for rec in records:
        text = f"[{dataset_name}] " + " | ".join(
            f"{k}: {v}" for k, v in rec.items() if v and k != "document_id"
        )
        chunks.append(text)
    return chunks