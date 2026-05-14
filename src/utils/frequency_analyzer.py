import hashlib


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def analyze(sanitized_term: str, results: list) -> list:
    """
    For each result URL, count how many times each token of the sanitized
    search term appears in the URL string. Only non-zero counts are returned.

    Returns a list of dicts: {result_id, token, frequency}
    """
    tokens = sanitized_term.lower().split()
    freq_rows = []
    for r in results:
        url = r.get("url", "").lower()
        if not url:
            continue
        result_id = _md5(r["url"])
        for token in tokens:
            count = url.count(token)
            if count > 0:
                freq_rows.append({
                    "result_id": result_id,
                    "token": token,
                    "frequency": count,
                })
    return freq_rows
