from backend.utils.config import SEARCH_API
from frontend.components.api_handler import api_request

def search_documents(query):
    return api_request("GET", SEARCH_API, params={"q": query})