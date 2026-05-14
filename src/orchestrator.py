from pathlib import Path

from utils.constants import PREDEFINED_SEARCHES, SEARCH_ENGINES
from utils.sanitize_utils import sanitize_query
from utils.ocr_utils import extract_urls_from_screenshot
from utils.frequency_analyzer import analyze
from utils.search_filter_utils import dedupe_and_filter_ads
from utils.db_utils import (
    start_batch_run, complete_batch_run,
    start_run, complete_run,
    insert_results, insert_frequencies,
)
from search import search

_SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"

if __name__ == "__main__":
    term = PREDEFINED_SEARCHES[0]
    sanitized_term = sanitize_query(term)
    print(f"Query     : {term}")
    print(f"Sanitized : {sanitized_term}\n")

    batch_id = start_batch_run()

    for engine in SEARCH_ENGINES:

        run_id = start_run(sanitized_term, engine, batch_id)

        # --- Extract (Selenium) ---
        results = search(sanitized_term, engine, run_id)
        print(f"\n[{engine}] {len(results)} raw results")

        # --- Extract (OCR cross-check) ---
        screenshot_path = str(_SCREENSHOT_DIR / f"run_id_{run_id}.png")
        ocr_urls = extract_urls_from_screenshot(screenshot_path)
        if ocr_urls:
            print(f"[{engine}] OCR found {len(ocr_urls)} URLs — merging")
            ocr_results = [{"url": u, "title": ""} for u in ocr_urls]
            results = results + ocr_results

        # --- Transform ---
        clean_results = dedupe_and_filter_ads(results)

        # --- Load ---
        insert_results(run_id, clean_results)

        freq_data = analyze(sanitized_term, clean_results)
        insert_frequencies(run_id, freq_data)

        complete_run(run_id)

    complete_batch_run(batch_id)
