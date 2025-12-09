from backend.utils.config import ADMIN_API
from frontend.components.api_handler import api_request

def get_system_stats():
    return api_request("GET", f"{ADMIN_API}/stats")

def get_indexing_errors():
    return api_request("GET", f"{ADMIN_API}/errors")

def get_count_validation():
    return api_request("GET", f"{ADMIN_API}/count")