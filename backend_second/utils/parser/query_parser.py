import re
import dateparser
from datetime import datetime
from typing import Optional, Dict
from transformers import pipeline
from dateutil.relativedelta import relativedelta

_classifier = None
CANDIDATE_LABELS = ["transaction", "product", "services", "saved_payment"]

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return _classifier


def preprocess_query(query: str) -> str:
    return re.sub(r"[^\w\s]", "", query.lower().strip())


def keyword_based_intent(query: str) -> Optional[str]:
    if any(w in query for w in ["pay", "send", "transfer", "transaction", "money", "purchase", "expense", "spent"]):
        return "transaction"
    if any(w in query for w in ["buy", "purchase", "order", "product", "item"]):
        return "product"
    if any(w in query for w in ["topup", "recharge", "electricity", "internet", "water", "bill", "utility", "service"]):
        return "services"
    if any(w in query for w in ["saved", "payee", "recipient", "saved payment", "template"]):
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
    _amount_pattern = re.compile(r"(?:rs\.?|₹|amount|payment)\s*(?:is\s*)?([\d,]+(?:\.\d{1,2})?)")

    match = _amount_pattern.search(query.lower())
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
        (r"\b(at least|minimum)\s+(rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)", ">="),
        (r"\b(at most|maximum)\s+(rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)", "<="),
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

    # Relative date patterns
    relative_map = {
        "last month": (relativedelta(months=-1), "month"),
        "this month": (relativedelta(months=0), "month"),
        "last week": (relativedelta(weeks=-1), "week"),
        "last 7 days": (relativedelta(days=-7), "days"),
        "last 30 days": (relativedelta(days=-30), "days"),
        "this week": (relativedelta(weeks=0), "week"),
        "yesterday": (relativedelta(days=-1), "day"),
        "today": (relativedelta(days=0), "day"),
    }

    for phrase, (delta, unit) in relative_map.items():
        if phrase in query:
            if unit == "month":
                start = (now.replace(day=1) + delta).replace(day=1)
                end = (start + relativedelta(months=1) - relativedelta(days=1))
            elif unit == "week":
                start = (now + delta - relativedelta(days=now.weekday()))
                end = start + relativedelta(days=6)
            elif unit == "days":
                start = now + delta
                end = now
            else:  # day
                start = now + delta
                end = start

            return {
                "operator": "between",
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }

    # Absolute date patterns
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
        (r"\b(before|until|till)\b\s+([a-zA-Z0-9 ,/-]+)", "<"),
        (r"\b(on|for)\b\s+([a-zA-Z0-9 ,/-]+)", "==")
    ]:
        match = re.search(pattern, query)
        if match:
            parsed = dateparser.parse(match.group(2).strip())
            if parsed:
                return {"operator": operator, "date": parsed.strftime("%Y-%m-%d")}

    return None

def parse_query(query: str) -> Dict:
    raw_query = query
    preprocessed = preprocess_query(query)

    return {
        "raw_query": raw_query,
        "intent": detect_intent(preprocessed),
        "amount": extract_amount(query),
        "amount_filter": extract_amount_filter(query),
        "date": extract_date(query),
        "date_filter": extract_date_filter(query)
    }