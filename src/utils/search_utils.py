import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).parent / "src"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def _get_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver




def google_search(term: str) -> list:
    url = f"https://www.google.com/search?q={quote_plus(term)}"
    driver = _get_driver()
    results = []
    try:
        print(f"[Search] Loading: {url}")
        driver.get(url)
        time.sleep(4)

        print(f"[Debug] Current URL : {driver.current_url}")
        print(f"[Debug] Page title  : {driver.title}")

        driver.save_screenshot("./src/screenshots/debug_screenshot.png")

        # h3 tags inside #rso are Google's organic result titles; their
        # ancestor <a> carries the destination URL.
        title_elems = driver.find_elements("css selector", "#rso h3")
        print(f"[Debug] h3 count in #rso: {len(title_elems)}")

        for h3 in title_elems:
            title = h3.text.strip()
            if not title:
                continue
            try:
                anchor = h3.find_element("xpath", "ancestor::a[@href][1]")
                href = anchor.get_attribute("href")
            except Exception:
                continue
            if not href or not href.startswith("http"):
                continue
            results.append({
                "url": href,
                "title": title
            })
    except Exception as e:
        print(e)
    finally:
        driver.quit()

    return results


