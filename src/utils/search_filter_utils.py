from utils.constants import AD_URL_SIGNALS,  AD_TITLE_SIGNALS
"""
A note on ad detection — the parsers in search_browser_utils.py already target organic-only containers 
(#rso for Google, li.b_algo for Bing, h3.title for Yahoo), so very few ads slip through at the DOM level.
 
The filter_ads URL/title signal check in search_filter_utils.py is the second line of defense for anything that 
leaks through.
"""
def _is_ad(url: str, title: str) -> bool:
    url_l = url.lower()
    title_l = title.lower()
    return (
        any(s in url_l for s in AD_URL_SIGNALS)
        or any(s in title_l for s in AD_TITLE_SIGNALS)
    )


def filter_ads(results: list) -> list:
    """Step 7 — remove any result whose URL or title matches known ad signals."""
    clean = [r for r in results if not _is_ad(r.get("url", ""), r.get("title", ""))]
    print(f"[Filter] Ads removed: {len(results) - len(clean)}  remaining: {len(clean)}")
    return clean


def deduplicate(results: list) -> list:
    """Remove results with duplicate URLs, preserving first-seen order."""
    seen = set()
    unique = []
    for r in results:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(r)
    print(f"[Filter] Duplicates removed: {len(results) - len(unique)}  remaining: {len(unique)}")
    return unique


def extract_urls(results: list) -> list:
    """Transform — pull the URL string from each result dict."""
    return [r["url"] for r in results if r.get("url")]


def dedupe_and_filter_ads(results: list) -> tuple:
    """
    Full Transform step of ETL:
      1. filter_ads   — drop ad results
      2. deduplicate  — one result per unique URL
    Returns clean_results
    """
    return deduplicate(filter_ads(results))
