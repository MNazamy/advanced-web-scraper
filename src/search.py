import time
from pathlib import Path
from urllib.parse import quote_plus

from utils.search_browser_utils import get_driver, ENGINE_CONFIGS

# ---------------------------------------------------------------------------
# Generic search runner — shared browser lifecycle for every engine
# ---------------------------------------------------------------------------

_SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"


def search(term: str, engine: str, run_id: int, pages: int = 2) -> list:
    engine_config = ENGINE_CONFIGS[engine]
    encoded_term = quote_plus(term)
    driver = get_driver()
    all_results = []

    _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if engine_config.get("use_scroll"):
            # DuckDuckGo uses infinite scroll — load once, scroll for extra pages
            url = engine_config["get_page_url"](encoded_term, 1)
            print(f"[Search] Loading: {url}")
            driver.get(url)
            time.sleep(4)

            for scroll in range(pages - 1):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                print(f"[Search] {engine} scroll {scroll + 1}/{pages - 1}")
                time.sleep(3)

            driver.save_screenshot(str(_SCREENSHOT_DIR / f"run_id_{run_id}_p1.png"))
            results = engine_config["parser_function"](driver)
            print(f"[Debug] {engine} returned {len(results)} results after {pages} scroll(s)")
            all_results.extend(results)

        else:
            for page in range(1, pages + 1):
                url = engine_config["get_page_url"](encoded_term, page)
                print(f"[Search] Loading page {page}/{pages}: {url}")
                driver.get(url)
                time.sleep(4)

                print(f"[Debug] Current URL : {driver.current_url}")
                print(f"[Debug] Page title  : {driver.title}")

                driver.save_screenshot(str(_SCREENSHOT_DIR / f"run_id_{run_id}_p{page}.png"))

                page_results = engine_config["parser_function"](driver)
                print(f"[Debug] {engine} page {page} returned {len(page_results)} results")
                all_results.extend(page_results)

    except Exception as e:
        print(f"[Search ERROR] {e}")
    finally:
        driver.quit()

    return all_results
