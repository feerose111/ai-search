import re

def clean_text(text):
    """Basic cleaning: lowercase, remove symbols/emoticons, trim spaces."""
    if not isinstance(text, str):
        return str(text)
    text = text.lower()
    text = re.sub(r"[^\w\s.>-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

TEMPLATES = {
    "transaction": lambda data: (
        f"payment to {clean_text(data['metadata'].get('merchant_name', 'unknown merchant'))} "
        f"for {clean_text(data['metadata'].get('description', 'no description'))} "
        f"via {clean_text(data['metadata'].get('properties', {}).get('service_name', 'unknown services'))}"
    ),
    "saved_payment": lambda data: (
        f"saved payment: {clean_text(data['metadata'].get('template_name', 'untitled template'))} "
        f"to {clean_text(data['metadata'].get('payee_name', 'unknown payee'))} "
        f"for {clean_text(data['metadata'].get('description', ''))}"
    ),
    "service": lambda data: (
        f"faq: {clean_text(data['metadata'].get('title', 'untitled faq'))}. "
        f"{clean_text(data['metadata'].get('content', ''))}"
    ),
    "product": lambda data: (
        f"product: {clean_text(data['metadata'].get('product_name', 'unnamed product'))}. "
        f"{clean_text(data['metadata'].get('description', ''))} "
        f"by {clean_text(data['metadata'].get('vendor', 'unknown vendor'))}"
    )
}