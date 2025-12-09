import requests

def api_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=15, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")