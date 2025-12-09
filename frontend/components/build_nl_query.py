def build_query(base_query,filters):
    query_parts = [base_query]


    if filters['type']:
        query_parts.append(f"Type: {' or '.join(filters['type'])}")

    if filters['category']:
        query_parts.append(f"Category: {filters['category']}")

    if filters['date_from'] and filters['date_to']:
        from_str = filters['date_from'].strftime("%Y-%m-%d")
        to_str = filters['date_to'].strftime("%Y-%m-%d")
        query_parts.append(f"between {from_str} and {to_str}")

    if filters['min_amt'] is not None and filters['max_amt'] is not None:
        query_parts.append(f"amount from {filters['min_amt']} to {filters['max_amt']}")

    return " ".join(query_parts)