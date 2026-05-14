from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_driver():
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


# ---------------------------------------------------------------------------
# Per-engine result parsers
# Each receives the live driver and returns a list of {url, title} dicts.
# ---------------------------------------------------------------------------

def _parse_google(driver):
    results = []
    for h3 in driver.find_elements("css selector", "#rso h3"):
        title = h3.text.strip()
        if not title:
            continue
        try:
            anchor = h3.find_element("xpath", "ancestor::a[@href][1]")
            href = anchor.get_attribute("href")
        except Exception:
            continue
        if href and href.startswith("http"):
            results.append({"url": href, "title": title})
    return results


def _parse_bing(driver):
    results = []
    for anchor in driver.find_elements("css selector", "li.b_algo h2 a"):
        href = anchor.get_attribute("href")
        title = anchor.text.strip()
        if href and href.startswith("http") and title:
            results.append({"url": href, "title": title})
    return results


def _parse_yahoo(driver):
    results = []
    for h3 in driver.find_elements("css selector", "h3.title"):
        title = h3.text.strip()
        if not title:
            continue
        try:
            anchor = h3.find_element("xpath", "ancestor::a[@href][1]")
            href = anchor.get_attribute("href")
        except Exception:
            continue
        if href and href.startswith("http"):
            results.append({"url": href, "title": title})
    return results


def _parse_duckduckgo(driver):
    results = []
    for anchor in driver.find_elements("css selector", "[data-testid='result'] h2 a"):
        href = anchor.get_attribute("href")
        title = anchor.text.strip()
        if href and href.startswith("http") and title:
            results.append({"url": href, "title": title})
    return results


# ---------------------------------------------------------------------------
# Engine configurations
# get_page_url(term, page) — term is already URL-encoded, page is 1-indexed.
# use_scroll=True means pagination is done via JS scroll, not URL navigation.
# ---------------------------------------------------------------------------

ENGINE_CONFIGS = {
    "google": {
        "get_page_url": lambda term, page: (
            f"https://www.google.com/search?q={term}&start={(page - 1) * 10}"
        ),
        "parser_function": _parse_google,
    },
    "bing": {
        "get_page_url": lambda term, page: (
            f"https://www.bing.com/search?q={term}&first={(page - 1) * 10 + 1}"
        ),
        "parser_function": _parse_bing,
    },
    "yahoo": {
        "get_page_url": lambda term, page: (
            f"https://search.yahoo.com/search?p={term}&b={(page - 1) * 10 + 1}"
        ),
        "parser_function": _parse_yahoo,
    },
    "duckduckgo": {
        "get_page_url": lambda term, page: f"https://duckduckgo.com/?q={term}",
        "parser_function": _parse_duckduckgo,
        "use_scroll": True,
    },
}
