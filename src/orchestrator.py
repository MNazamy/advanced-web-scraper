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
    create_topic,
)
from search import search

_SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"


def run_pipeline(term: str, engines=None, pages=2, topic_id=None, on_step=None) -> int:
    """
    on_step(engine, substep, status) — engine is None for global steps,
    substep is None for engine-level status changes.
    """
    if engines is None:
        engines = SEARCH_ENGINES

    def _s(engine, substep, status):
        if on_step:
            on_step(engine, substep, status)

    _s(None, "sanitize", "running")
    sanitized_term = sanitize_query(term)
    print(f"Query     : {term}")
    print(f"Sanitized : {sanitized_term}\n")
    _s(None, "sanitize", "done")

    batch_id = start_batch_run(topic_id=topic_id)

    for engine in engines:
        engine_pages = pages[engine] if isinstance(pages, dict) else pages
        _s(engine, None, "running")

        _s(engine, "scraping", "running")
        run_id = start_run(sanitized_term, engine, batch_id)
        results = search(sanitized_term, engine, run_id, pages=engine_pages)
        print(f"\n[{engine}] {len(results)} raw results across {engine_pages} page(s)")
        _s(engine, "scraping", "done")

        _s(engine, "ocr", "running")
        ocr_results = []
        for page in range(1, engine_pages + 1):
            screenshot_path = _SCREENSHOT_DIR / f"run_id_{run_id}_p{page}.png"
            if screenshot_path.exists():
                ocr_urls = extract_urls_from_screenshot(str(screenshot_path))
                if ocr_urls:
                    print(f"[{engine}] OCR page {page}: {len(ocr_urls)} URLs")
                    ocr_results.extend({"url": u, "title": ""} for u in ocr_urls)
        if ocr_results:
            print(f"[{engine}] OCR total: {len(ocr_results)} URLs — merging")
            results = results + ocr_results
        _s(engine, "ocr", "done")

        _s(engine, "filter", "running")
        clean_results = dedupe_and_filter_ads(results)
        _s(engine, "filter", "done")

        _s(engine, "frequency", "running")
        freq_data = analyze(sanitized_term, clean_results)
        _s(engine, "frequency", "done")

        _s(engine, "store", "running")
        insert_results(run_id, clean_results)
        insert_frequencies(run_id, freq_data)
        complete_run(run_id)
        _s(engine, "store", "done")

        _s(engine, None, "done")

    complete_batch_run(batch_id)
    return batch_id


if __name__ == "__main__":
    run_pipeline(PREDEFINED_SEARCHES[0])
