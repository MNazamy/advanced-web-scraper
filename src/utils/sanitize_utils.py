from utils.constants import FILLERS_AND_DISCOURSE_MARKERS

def sanitize_query(query: str) -> str:
    words = query.split()
    kept = [w.lower() for w in words if w.lower() not in FILLERS_AND_DISCOURSE_MARKERS]
    return " ".join(kept)
