import hashlib

import mysql.connector
from mysql.connector import Error

from utils.config import DB_CONFIG


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[DB ERROR] {e}")
        raise


def _md5(text: str) -> str:
    """Matches MySQL's MD5() so Python-computed IDs align with generated columns."""
    return hashlib.md5(text.encode()).hexdigest()

def start_batch_run() -> int:
    """
    Ensure query_term and engine exist, open a search_run row, return run_id.
    search_start_timestamp is set automatically by MySQL DEFAULT CURRENT_TIMESTAMP.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO batch_runs (batch_start_timestamp) VALUES (NOW())"
        )
        conn.commit()
        batch_id = cursor.lastrowid
        print(f"[DB] Opened BATCH job ID: #{batch_id}")
        return batch_id
    finally:
        cursor.close()
        conn.close()


def complete_batch_run(batch_id: int):
    """Stamp search_completion_timestamp on the run row."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE batch_runs SET batch_completion_timestamp = NOW() WHERE batch_id = %s",
            (batch_id,)
        )
        conn.commit()
        print(f"[DB] Closed BATCH run #{batch_id}")
    finally:
        cursor.close()
        conn.close()


def start_run(query: str, engine: str, batch_id: int) -> int:
    """
    Ensure query_term and engine exist, open a search_run row, return run_id.
    search_start_timestamp is set automatically by MySQL DEFAULT CURRENT_TIMESTAMP.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Upsert query term — INSERT IGNORE skips if the MD5 PK already exists
        cursor.execute(
            "INSERT IGNORE INTO query_terms (query_term) VALUES (%s)",
            (query,)
        )
        query_id = _md5(query)

        cursor.execute(
            "SELECT search_engine_id FROM search_engines WHERE search_engine_name = %s",
            (engine,)
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Unknown search engine: '{engine}'. Add it to search_engines first.")
        engine_id = row[0]

        cursor.execute(
            "INSERT INTO search_runs (query_id, search_engine_id, batch_id) VALUES (%s, %s, %s)",
            (query_id, engine_id, batch_id)
        )
        conn.commit()
        run_id = cursor.lastrowid
        print(f"[DB] Opened run #{run_id} — query_id={query_id[:8]}... engine={engine}")
        return run_id
    finally:
        cursor.close()
        conn.close()


def complete_run(run_id: int):
    """Stamp search_completion_timestamp on the run row."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE search_runs SET search_completion_timestamp = NOW() WHERE run_id = %s",
            (run_id,)
        )
        conn.commit()
        print(f"[DB] Closed run #{run_id}")
    finally:
        cursor.close()
        conn.close()


def insert_results(run_id: int, results: list):
    """
    Write scraped results to search_results (deduplicated by URL hash) and
    link them to this run via run_results.
    INSERT IGNORE on both tables means re-scraping the same URL is safe.
    """
    if not results:
        return
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for item in results:
            url = item.get("url", "").strip()
            if not url:
                continue
            title   = item.get("title", "")

            # Create unique entry for this search result
            cursor.execute(
                "INSERT IGNORE INTO search_results (url, title) VALUES (%s, %s)",
                (url, title)
            )
            
            # Add entry to bridge table
            cursor.execute(
                "INSERT IGNORE INTO run_results (run_id, result_id) VALUES (%s, MD5(%s))",
                (run_id, url)
            )
        conn.commit()
        print(f"[DB] Inserted {len(results)} results for run #{run_id}")
    finally:
        cursor.close()
        conn.close()
