from backend_second.utils.config import SEARCH_API_SECOND
from frontend_second.components.api_handler import api_request

def search_documents(query):
    return api_request("GET", SEARCH_API_SECOND, params={"q": query})