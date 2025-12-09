from diskcache import Cache
import hashlib
import json

cache = Cache("ai-search/.cache/query_results")

def _query_hash(parsed_query: dict, top_k: int) -> str:
    key_string = json.dumps({"query": parsed_query, "top_k": top_k}, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()

def get_cached(parsed_query: dict, top_k: int):
    return cache.get(_query_hash(parsed_query, top_k))

def store_cache(parsed_query: dict, top_k: int, result: list):
    cache.set(_query_hash(parsed_query, top_k), result, expire=3600)
