from backend.utils.config import UPSERT_API
from frontend.components.api_handler import api_request

def upsert_document(data):
    return api_request("POST", UPSERT_API, json=data)

def upsert_file(file):
    files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
    return api_request("POST", f"{UPSERT_API}/file", files=files)