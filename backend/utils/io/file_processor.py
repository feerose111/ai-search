import json, csv, io
from typing import Union, List, Dict, Any
from fastapi import HTTPException

def process_file(content: bytes, content_type: str) -> Union[dict, list]:
    if not content_type:
        raise HTTPException(400, "Content type is missing from uploaded file")

    if not content:
        raise HTTPException(400, "Uploaded file is empty")

    decode = content.decode('utf-8')

    if 'json' in content_type:
        try:
            return json.loads(decode)
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid JSON file")

    if 'csv' in content_type:
        try:
            csv_data = io.StringIO(decode)
            reader = csv.DictReader(csv_data)
            return [dict(row) for row in reader]
        except Exception:
            raise HTTPException(400, "Invalid CSV file")

    #only for edged cases
    #try processing without considering content_type
    try:
        return json.loads(decode)
    except json.JSONDecodeError:
        try:
            csv_data = io.StringIO(decode)
            return list(csv.DictReader(csv_data))
        except Exception:
            raise HTTPException(400, "Unsupported file format")
