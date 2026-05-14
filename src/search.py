from utils.search_browser_utils import get_driver, ENGINE_CONFIGS
from urllib.parse import quote_plus
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Generic search runner — shared browser lifecycle for every engine
# ---------------------------------------------------------------------------

_SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"


def search(term: str, engine: str, run_id: int) -> list:
    engine_config = ENGINE_CONFIGS[engine]
    url = engine_config["url"].format(term=quote_plus(term))
    driver = get_driver()
    results = []
    try:
        print(f"[Search] Loading: {url}")
        driver.get(url)
        time.sleep(4)

        print(f"[Debug] Current URL : {driver.current_url}")
        print(f"[Debug] Page title  : {driver.title}")

        _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(_SCREENSHOT_DIR / f"run_id_{run_id}.png"))

        results = engine_config["parser_function"](driver)
        print(f"[Debug] {engine} returned {len(results)} results")
    except Exception as e:
        print(f"[Search ERROR] {e}")
    finally:
        driver.quit()
    return results