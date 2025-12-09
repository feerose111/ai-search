import json

def normalize_document(data):
    """Normalize all document types to common schema"""
    doc_type = data.get("type")

    normalized = {
        "id": data.get("id"),
        "type": doc_type,
        "date": data.get("date") or data.get("created_at") or data.get("updated_at"),
        "user_id": data.get("user_id", "00000"),
        "category": data.get("category", "uncategorized"),
        "text": "",
        "metadata": {}
    }

    if doc_type == "product":
        normalized["amount"] = float(data.get("price", 0))
    elif doc_type == "services":
        normalized["amount"] = 0.0
    else:
        normalized["amount"] = float(data.get("amount", 0))

    # Preserve all original data in metadata
    original_fields = {k: v for k, v in data.items()
                       if k not in normalized and not k.startswith('_')}

    props = original_fields.get("properties")
    if isinstance(props, str):
        try:
            original_fields["properties"] = json.loads(props)
        except json.JSONDecodeError:
            original_fields["properties"] = {}

    normalized["metadata"] = original_fields
    print(normalized["metadata"])
    return normalized