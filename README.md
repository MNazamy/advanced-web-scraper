# Advanced Web Scraper

A multi-engine search scraper with a web GUI that implements a full ETL pipeline: extracting search results from Google, Bing, Yahoo, and DuckDuckGo across multiple pages, transforming them (ad removal, deduplication, frequency analysis), and loading them into a MySQL database. Results are organised by **Topics** for historical comparison across batch runs.

---

## Prerequisites

Install these before anything else:

| Dependency | Windows | macOS |
|---|---|---|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) | `brew install python` |
| MySQL 8.0+ | [dev.mysql.com](https://dev.mysql.com/downloads/) | `brew install mysql` |
| Google Chrome | [google.com/chrome](https://www.google.com/chrome/) | [google.com/chrome](https://www.google.com/chrome/) |
| Tesseract OCR | `winget install UB-Mannheim.TesseractOCR` | `brew install tesseract` |

---

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd advanced-web-scraper
```

### 2. Start MySQL

**Windows** (run as Administrator):
```powershell
net start MySQL80
```

**macOS**:
```bash
brew services start mysql
```

### 3. Create and activate a virtual environment

**Windows**:
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the database connection

Edit `src/utils/config.py` and fill in your MySQL credentials:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD_HERE",
    "database": "MY_CUSTOM_BOT",
}
```

### 6. Initialize the database

**Windows**:
```powershell
Get-Content src/scripts/init_database.sql | mysql -u root -p
```

**macOS**:
```bash
mysql -u root -p < src/scripts/init_database.sql
```

This creates the `MY_CUSTOM_BOT` database and all tables from scratch. Re-run this any time you need to reset the database.

---

## Running the web GUI (recommended)

With the venv active, start the Flask server from the `src/` directory:

**Windows**:
```powershell
cd src
python app.py
```

**macOS**:
```bash
cd src
python3 app.py
```

Then open `http://localhost:5000` in your browser.

### Search page features

- **Topic selector** — Associate a search with a named topic (create one inline or pick an existing one). Results from multiple batch runs accumulate under the same topic.
- **Search term validation** — The query must contain at least 4 meaningful words after common filler words are stripped. An inline error explains how many words remain if the check fails.
- **Engine toggles** — Enable or disable individual engines (Google, Bing, Yahoo, DuckDuckGo) per search.
- **Per-engine page count** — Set how many result pages to scrape independently for each engine (default 2, max 10). Google/Bing/Yahoo use paginated URLs; DuckDuckGo uses scroll-based loading.
- **Live pipeline progress** — A progress panel shows each step in real time: Sanitize → per-engine Scraping → OCR cross-check → Filter & deduplicate → Frequency analysis → Store to database, each with a pending / running / done indicator.
- **Ranked results** — URLs are displayed ranked highest to lowest by total frequency score. Zero-match URLs are excluded.

### Topics page (`/topics`)

- View all topics with batch run count and last run date.
- Click any topic card to expand and see its aggregated results across all batch runs, each result showing its frequency score and how many batches it appeared in.
- Create new topics directly from this page.

---

## Running the scraper (CLI)

With the venv active:

**Windows**:
```powershell
python src/orchestrator.py
```

**macOS**:
```bash
python3 src/orchestrator.py
```

The orchestrator runs through all four search engines for the first predefined search term. For each engine it:
1. Sanitizes the query (strips filler words)
2. Scrapes each result page via Selenium, saving screenshots to `screenshots/`
3. Runs OCR on every screenshot to cross-check URLs
4. Filters ads and deduplicates results
5. Loads clean results and term frequency data into MySQL

To change the search term, edit `src/utils/constants.py` and update `PREDEFINED_SEARCHES[0]`.

---

## Project structure

```
advanced-web-scraper/
├── requirements.txt
├── src/
│   ├── app.py                       # Flask web server — routes and job threading
│   ├── orchestrator.py              # ETL pipeline — orchestrates all engines per batch
│   ├── search.py                    # Browser lifecycle + multi-page scraping per engine
│   ├── templates/
│   │   ├── index.html               # Search page UI
│   │   └── topics.html              # Topics history page UI
│   ├── utils/
│   │   ├── config.py                # DB credentials (gitignored)
│   │   ├── constants.py             # Search terms, engine list, filler word list
│   │   ├── search_browser_utils.py  # Chrome driver + per-engine DOM parsers + page URLs
│   │   ├── search_filter_utils.py   # Ad removal and deduplication
│   │   ├── sanitize_utils.py        # Strips filler words from queries
│   │   ├── ocr_utils.py             # Tesseract OCR on screenshots
│   │   ├── frequency_analyzer.py    # Term frequency counting per URL
│   │   └── db_utils.py              # All MySQL read/write functions
│   └── scripts/
│       └── init_database.sql        # Full DB schema (run once to set up)
└── screenshots/                     # Auto-created, one PNG per page per search run
```

---

## Database schema

| Table | Description |
|---|---|
| `topics` | Named research areas; groups batch runs for historical comparison |
| `search_engines` | Lookup table for engine names (google, bing, yahoo, duckduckgo) |
| `query_terms` | Sanitized search terms, PK is `MD5(query_term)` |
| `batch_runs` | One row per orchestrator execution, optionally linked to a topic |
| `search_runs` | One row per engine per batch, tracks start/end timestamps |
| `search_results` | Deduplicated URLs and titles, PK is `MD5(url)` |
| `run_results` | Bridge table linking runs to results |
| `term_frequencies` | Per-token frequency count of search term words in each result URL |

---

## Troubleshooting

**`[OCR ERROR] tesseract is not installed`**
Tesseract is installed but not on your PATH, or not installed at all.
- Windows: run `winget install UB-Mannheim.TesseractOCR`, reopen your terminal, and verify `tesseract --version`. If it still fails, check that `C:\Program Files\Tesseract-OCR` is in your system PATH.
- macOS: run `brew install tesseract`, then verify with `tesseract --version`.

**`Access denied for user 'root'@'localhost'`**
Wrong password in `src/utils/config.py`, or the MySQL service is not running. Check with:
- Windows: `Get-Service -Name "mysql*"`
- macOS: `brew services list | grep mysql`

**`Found 0 results` for an engine**
Open the screenshot in `screenshots/` — if it shows a CAPTCHA or consent page the engine detected the headless browser. DuckDuckGo is most prone to this. Try reducing the number of pages or waiting before re-running.

**`venv` not found / package errors**
Make sure the virtual environment is activated before running anything:
- Windows: `venv\Scripts\activate`
- macOS: `source venv/bin/activate`

**Port 5000 already in use (macOS)**
macOS Monterey and later use port 5000 for AirPlay Receiver. Either disable AirPlay Receiver in System Settings → General → AirDrop & Handoff, or start the server on a different port:
```bash
python3 src/app.py --port 5001
```
Then open `http://localhost:5001`.
