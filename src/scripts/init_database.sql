DROP DATABASE IF EXISTS MY_CUSTOM_BOT;
CREATE DATABASE MY_CUSTOM_BOT;
USE MY_CUSTOM_BOT;

-- -------------------------------------------------------
-- search_engines  (small lookup, plain int PK is fine)
-- -------------------------------------------------------
CREATE TABLE search_engines (
    search_engine_id   INT          AUTO_INCREMENT PRIMARY KEY,
    search_engine_name VARCHAR(20)  NOT NULL UNIQUE
);

INSERT INTO search_engines (search_engine_name) VALUES
    ('google'),
    ('bing'),
    ('yahoo'),
    ('duckduckgo');

-- -------------------------------------------------------
-- query_terms
-- query_id is a STORED generated column: MD5(query_term).
-- Identical query strings always produce the same ID, so
-- INSERT IGNORE deduplicates without a separate lookup.
-- -------------------------------------------------------
CREATE TABLE query_terms (
    query_term VARCHAR(2000)                   NOT NULL,
    query_id   CHAR(32) AS (MD5(query_term))   STORED,
    PRIMARY KEY (query_id)
);


-- -------------------------------------------------------
-- search_runs  (one row per scrape execution)
-- -------------------------------------------------------
CREATE TABLE batch_runs (
    batch_id                   INT       AUTO_INCREMENT PRIMARY KEY,
    batch_start_timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_completion_timestamp TIMESTAMP
);

-- -------------------------------------------------------
-- search_runs  (one row per scrape execution)
-- -------------------------------------------------------
CREATE TABLE search_runs (
    run_id                      INT       AUTO_INCREMENT PRIMARY KEY,
    query_id                    CHAR(32)  NOT NULL,
    batch_id                    INT       NOT NULL,
    search_engine_id            INT       NOT NULL,
    search_start_timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    search_completion_timestamp TIMESTAMP,
    FOREIGN KEY (query_id)         REFERENCES query_terms(query_id),
    FOREIGN KEY (search_engine_id) REFERENCES search_engines(search_engine_id),
    FOREIGN KEY (batch_id)         REFERENCES batch_runs(batch_id)

);

-- -------------------------------------------------------
-- search_results
-- result_id is a STORED generated column: MD5(url).
-- The same URL scraped across many runs is stored once here;
-- the run_results bridge records which runs returned it.
-- -------------------------------------------------------
CREATE TABLE search_results (
    url       VARCHAR(2000)                NOT NULL,
    title     VARCHAR(2000),
    result_id CHAR(32) AS (MD5(url))       STORED,
    PRIMARY KEY (result_id)
);

-- -------------------------------------------------------
-- run_results  (many-to-many: runs ↔ results)
-- -------------------------------------------------------
CREATE TABLE run_results (
    run_id    INT      NOT NULL,
    result_id CHAR(32) NOT NULL,
    PRIMARY KEY (run_id, result_id),
    FOREIGN KEY (run_id)    REFERENCES search_runs(run_id),
    FOREIGN KEY (result_id) REFERENCES search_results(result_id)
);
