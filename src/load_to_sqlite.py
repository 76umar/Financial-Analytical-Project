"""
Stage 1: Load raw CSVs into a SQLite database (data/processed/financials.db).

Creates two normalised tables:
  - companies(ticker PK, company_name, sector)
  - financials(id PK, ticker FK, fiscal_year, period_ending, revenue_musd,
               revenue_growth_pct, net_income_musd, eps_diluted, pe_ratio,
               debt_to_equity, roe_pct)

This mirrors Stage 1 of the project plan: "Write your first SQL schema and
load the data into a SQLite database."
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "financials.db")

SCHEMA = """
DROP TABLE IF EXISTS financials;
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    ticker       TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector       TEXT NOT NULL
);

CREATE TABLE financials (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker             TEXT NOT NULL REFERENCES companies(ticker),
    fiscal_year        TEXT NOT NULL,
    period_ending      TEXT,
    revenue_musd       REAL,
    revenue_growth_pct REAL,
    net_income_musd    REAL,
    eps_diluted        REAL,
    pe_ratio           REAL,
    debt_to_equity     REAL,
    roe_pct            REAL,
    UNIQUE(ticker, fiscal_year)
);
"""


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def to_float(v):
    if v is None or v == "" or v == "None":
        return None
    return float(v)


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    companies = load_csv(os.path.join(RAW_DIR, "companies.csv"))
    cur.executemany(
        "INSERT INTO companies (ticker, company_name, sector) VALUES (?, ?, ?)",
        [(c["ticker"], c["company_name"], c["sector"]) for c in companies],
    )

    financials = load_csv(os.path.join(RAW_DIR, "raw_financials.csv"))
    rows = [
        (
            f["ticker"], f["fiscal_year"], f["period_ending"],
            to_float(f["revenue_musd"]), to_float(f["revenue_growth_pct"]),
            to_float(f["net_income_musd"]), to_float(f["eps_diluted"]),
            to_float(f["pe_ratio"]), to_float(f["debt_to_equity"]),
            to_float(f["roe_pct"]),
        )
        for f in financials
    ]
    cur.executemany(
        """INSERT INTO financials
           (ticker, fiscal_year, period_ending, revenue_musd, revenue_growth_pct,
            net_income_musd, eps_diluted, pe_ratio, debt_to_equity, roe_pct)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )

    conn.commit()
    n_companies = cur.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    n_financials = cur.execute("SELECT COUNT(*) FROM financials").fetchone()[0]
    print(f"Loaded {n_companies} companies and {n_financials} financial records into {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
