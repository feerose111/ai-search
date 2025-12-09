import re
import dateparser
from datetime import datetime
from typing import Optional, Dict
from transformers import pipeline
from dateutil.relativedelta import relativedelta

_classifier = None
CANDIDATE_LABELS = ["transaction", "product", "services", "saved_payment", "general"]

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return _classifier

def preprocess_query(query: str) -> str:
    return re.sub(r"[^\w\s]", "", query.lower().strip())

def keyword_based_intent(query: str) -> Optional[str]:
    if any(w in query for w in ["pay", "send", "transfer", "transaction", "money"]):
        return "transaction"
    if any(w in query for w in ["buy", "purchase", "order", "product", "item", "phone", "laptop"]):
        return "product"
    if any(w in query for w in ["topup", "recharge", "electricity", "internet", "water", "bill"]):
        return "services"
    if any(w in query for w in ["saved", "payee", "recipient", "saved payment"]):
        return "saved_payment"
    return None

def ml_based_intent(query: str) -> str:
    classifier = get_classifier()
    result = classifier(query, CANDIDATE_LABELS)
    return result["labels"][0]

def detect_intent(query: str) -> str:
    preprocessed = preprocess_query(query)
    return keyword_based_intent(preprocessed) or ml_based_intent(preprocessed)

def extract_amount(query: str) -> Optional[float]:
    pattern = r"(?:rs\.?|₹|amount|payment)\s*(?:is\s*)?([\d,]+(?:\.\d{1,2})?)"
    match = re.search(pattern, query.lower())
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None

def extract_amount_filter(query: str) -> Optional[Dict]:
    query = query.lower()
    patterns = [
        (r"\b(greater than|more than|above|over)\s+(rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)", ">"),
        (r"\b(less than|below|under)\s+(rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)", "<"),
        (r"\b(equal to|exactly|equals)\s+(rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)", "="),
    ]
    for pattern, operator in patterns:
        match = re.search(pattern, query)
        if match:
            raw_amount = match.group(3).replace(",", "")
            try:
                return {"operator": operator, "amount": float(raw_amount)}
            except ValueError:
                pass
    return None


def extract_date(query: str) -> Optional[str]:
    parsed = dateparser.parse(query, settings={'PREFER_DATES_FROM': 'past'})
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    return None


def extract_date_filter(query: str) -> Optional[Dict]:
    query = query.lower()
    now = datetime.today()

    if "last month" in query:
        start = (now.replace(day=1) - relativedelta(months=1)).replace(day=1)
        end = start + relativedelta(months=1) - relativedelta(days=1)
        return {
            "operator": "between",
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d")
        }

    if "this month" in query:
        start = now.replace(day=1)
        end = (start + relativedelta(months=1)) - relativedelta(days=1)
        return {
            "operator": "between",
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d")
        }

    if "last week" in query:
        start = now - relativedelta(weeks=1, weekday=0)
        end = start + relativedelta(days=6)
        return {
            "operator": "between",
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d")
        }

    # Your previous patterns: between, after, before
    match = re.search(r"\bbetween\s+([a-zA-Z0-9 ,/-]+?)\s+and\s+([a-zA-Z0-9 ,/-]+)", query)
    if match:
        start_raw, end_raw = match.groups()
        start = dateparser.parse(start_raw)
        end = dateparser.parse(end_raw)
        if start and end:
            return {
                "operator": "between",
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }

    for pattern, operator in [
        (r"\b(after|since)\b\s+([a-zA-Z0-9 ,/-]+)", ">"),
        (r"\b(before|until|till)\b\s+([a-zA-Z0-9 ,/-]+)", "<")
    ]:
        match = re.search(pattern, query)
        if match:
            parsed = dateparser.parse(match.group(2).strip())
            if parsed:
                return {"operator": operator, "date": parsed.strftime("%Y-%m-%d")}
    
    return None


def parse_query(query: str) -> Dict:
    return {
        "raw_query": query,
        "intent": detect_intent(query),
        "amount": extract_amount(query),
        "amount_filter": extract_amount_filter(query),
        "date": extract_date(query),
        "date_filter": extract_date_filter(query),
    }
