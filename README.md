# Advanced Web Scraper

A multi-engine search scraper that implements a full ETL pipeline: extracting search results from Google, Bing, Yahoo, and DuckDuckGo, transforming them (ad removal, deduplication, frequency analysis), and loading them into a MySQL database.

---

## Prerequisites

Install these before anything else:

| Dependency | Install |
|---|---|
| Python 3.10+ | https://www.python.org/downloads/ |
| MySQL 8.0+ | https://dev.mysql.com/downloads/ |
| Google Chrome | https://www.google.com/chrome/ |
| Tesseract OCR | `winget install UB-Mannheim.TesseractOCR` |

---

## Setup

### 1. Clone the repo
```powershell
git clone <repo-url>
cd advanced-web-scraper
```

### 2. Start the mysql services
```powershell
Start-Process powershell -Verb RunAs -ArgumentList "net start MySQL80"
```

### 2. Create and activate the virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```



### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure the database connection
Edit `src/utils/config.py` and fill in your MySQL credentials:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD_HERE",
    "database": "MY_CUSTOM_BOT",
}
```

### 5. Initialize the database
```powershell
Get-Content src/scripts/init_database.sql | mysql -u root -p
```
This creates the `MY_CUSTOM_BOT` database and all tables from scratch.

---

## Running the web GUI (recommended)

With the venv active, start the Flask server from the `src/` directory:

```powershell
cd src
python app.py
```

Then open `http://localhost:5000` in your browser.

- Type any search term and press **Search** or hit Enter
- Toggle individual engine buttons (Google, Bing, Yahoo, DuckDuckGo) to choose which engines to query
- A live progress panel shows each engine's status (pending → running → done) with real-time checkmarks
- Results appear ranked from highest to lowest frequency score, with zero-match URLs excluded

---

## Running the scraper (CLI)

With the venv active:
```powershell
python src/orchestrator.py
```

The orchestrator will loop through all four search engines for the first predefined search term. For each engine it:
1. Sanitizes the query (strips filler words)
2. Runs the Selenium search and saves a screenshot to `screenshots/`
3. Runs OCR on the screenshot to cross-check URLs
4. Filters ads and deduplicates results
5. Loads clean results and term frequency data into MySQL

To change which search term is used, edit `src/utils/constants.py` and change `PREDEFINED_SEARCHES[0]`.

---

## Project structure

```
advanced-web-scraper/
├── requirements.txt
├── src/
│   ├── orchestrator.py          # Entry point — runs the full ETL loop
│   ├── search.py                # Generic browser runner (shared across engines)
│   ├── utils/
│   │   ├── config.py            # DB credentials (gitignored)
│   │   ├── constants.py         # Search terms, engine list, filler word list
│   │   ├── search_browser_utils.py  # Chrome driver + per-engine DOM parsers
│   │   ├── search_filter_utils.py   # Ad removal and deduplication
│   │   ├── sanitize_utils.py    # Strips filler words from queries
│   │   ├── ocr_utils.py         # Tesseract OCR on screenshots
│   │   ├── frequency_analyzer.py    # Term frequency counting per URL
│   │   └── db_utils.py          # All MySQL read/write functions
│   └── scripts/
│       └── init_database.sql    # Full DB schema (run once to set up)
└── screenshots/                 # Auto-created, one PNG per search run
```

---

## Database schema

| Table | Description |
|---|---|
| `search_engines` | Lookup table for engine names (google, bing, yahoo, duckduckgo) |
| `query_terms` | Sanitized search terms, PK is `MD5(query_term)` |
| `batch_runs` | One row per full execution of the orchestrator |
| `search_runs` | One row per engine per batch, tracks start/end timestamps |
| `search_results` | Deduplicated URLs and titles, PK is `MD5(url)` |
| `run_results` | Bridge table linking runs to results |
| `term_frequencies` | Per-token frequency count of search term words in each result URL |

---

## Troubleshooting

**`[OCR ERROR] tesseract is not installed`**
Tesseract binary is missing. Run `winget install UB-Mannheim.TesseractOCR` then reopen your terminal.

**`Access denied for user 'root'@'localhost'`**
Wrong MySQL password in `src/utils/config.py`, or the MySQL service isn't running.

**`Found 0 results` for an engine**
Check the screenshot in `screenshots/run_id_N.png` — if it shows a CAPTCHA or consent page, the engine detected the headless browser. DuckDuckGo is most prone to this.

**Package not found errors**
Make sure the venv is activated (`venv\Scripts\activate`) before running. All packages must be installed into the venv, not the system Python.
