import logging, json
from elasticsearch import Elasticsearch, exceptions
# Make sure this is imported

logging.basicConfig(level=logging.DEBUG)

INDEX_NAME = "esewa_index_data"  # existing index
QUERY_HISTORY_INDEX_NAME = "query_history"  # new index for query history

# Existing mapping for esewa_index_data (unchanged)
ESEWA_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "normalizer": {
                "lowercase_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase"]
                }
            }
        }
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "type": {
                "type": "keyword",  
                "normalizer": "lowercase_normalizer"
            },
            "user_id": {"type": "keyword"},
            "amount": {"type": "double"},
            "currency": {"type": "keyword"},
            "category": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
            },
            "description": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "date": {"type": "date"},
            "merchant_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "lowercase_normalizer"
                    }
                }
            },
            "status": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
            },
            "properties": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "keyword",
                        "normalizer": "lowercase_normalizer"
                    },
                    "ip": {"type": "ip"}
                }
            },
            "template_name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "payee_name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "created_at": {"type": "date"},
            "title": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "content": {"type": "text"},
            "language": {"type": "keyword"},
            "updated_at": {"type": "date"},
            "product_name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "price": {"type": "double"},
            "available": {"type": "boolean"},
            "vendor": {"type": "keyword"},
            "text": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "metadata": {
                "type": "object",
                "enabled": True
            },
        }
    }
}

# Mapping from your consumer's _ensure_index_exists method
QUERY_HISTORY_MAPPING = {
    "settings": {
        "analysis": {
            "normalizer": {
                "lowercase_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "query_id": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "raw_query": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "intent": {"type": "keyword"},
            "parsed_query": {
                "properties": {
                    "raw_query": {"type": "text"},
                    "intent": {"type": "keyword"},
                    "amount": {"type": "float"},
                    "amount_filter": {
                        "properties": {
                            "operator": {"type": "keyword"},
                            "value": {"type": "float"}
                        }
                    },
                    "date": {"type": "date"},
                    "date_filter": {
                        "properties": {
                            "operator": {"type": "keyword"},
                            "start": {"type": "date"},
                            "end": {"type": "date"}
                        }
                    }
                }
            },
            "date_filter": {
                "properties": {
                    "operator": {"type": "keyword"},
                    "start": {"type": "date"},
                    "end": {"type": "date"}
                }
            }
        }
    }
}


def get_es():
    return Elasticsearch("http://localhost:9200", verify_certs=False)


def create_index(es_client, index_name, mapping):
    try:
        if es_client.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists.")
        else:
            es_client.indices.create(index=index_name, body=mapping)
            print(f"✅ Created index '{index_name}' with provided mapping.")
    except exceptions.RequestError as e:
        print(f"⚠️ Failed to create index '{index_name}': {e}")


if __name__ == "__main__":
    es = get_es()

    # Create esewa_index_data with existing mapping
    create_index(es, INDEX_NAME, ESEWA_INDEX_MAPPING)

    # Create query history index with your consumer mapping
    create_index(es, QUERY_HISTORY_INDEX_NAME, QUERY_HISTORY_MAPPING)

    # Optional: print mappings for confirmation
    try:
        print("ESEWA_INDEX mapping:\n", json.dumps(es.indices.get_mapping(index=INDEX_NAME).body, indent=2))
        print(f"\n{QUERY_HISTORY_INDEX_NAME} mapping:\n", json.dumps(es.indices.get_mapping(index=QUERY_HISTORY_INDEX_NAME).body, indent=2))
    except Exception as e:
        print("Error fetching index mappings:", e)
