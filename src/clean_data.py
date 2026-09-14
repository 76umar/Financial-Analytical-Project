"""
Stage 2: Data cleaning with pandas.

Reads the raw financials table from SQLite, cleans it, and writes a
clean, analysis-ready table back into the database (financials_clean)
plus an exported CSV (data/processed/financials_clean.csv).

Cleaning steps:
  1. Drop the noisy "TTM" (trailing twelve months) rows -- we standardise
     on full fiscal years only so year-over-year comparisons are apples-to-apples.
  2. Compute net_profit_margin_pct = net_income / revenue * 100 for every
     row (more reliable than sourcing it separately, and lets us sanity-check
     against reported figures).
  3. Handle missing values: pe_ratio / roe_pct / debt_to_equity are left as
     NULL when a company had negative or de minimis earnings (P/E and ROE
     are not meaningful in that case) rather than being filled with 0,
     which would distort sector averages.
  4. Flag structurally negative-equity companies (Dell, HP Inc.) where
     debt_to_equity is negative because shareholders' equity itself is
     negative -- these are excluded from D/E sector averages but kept in
     the dataset (flag: negative_equity = 1).
  5. Remove duplicate (ticker, fiscal_year) rows, standardise column types.
"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "financials.db")
OUT_CSV = os.path.join(BASE_DIR, "data", "processed", "financials_clean.csv")


def main():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM financials", conn)
    companies = pd.read_sql_query("SELECT * FROM companies", conn)

    before = len(df)

    # 1. Drop duplicates on (ticker, fiscal_year)
    df = df.drop_duplicates(subset=["ticker", "fiscal_year"])

    # 2. Drop TTM rows -- keep only full fiscal years for clean YoY comparison
    df = df[df["fiscal_year"] != "TTM"].copy()

    # 3. Recompute net profit margin directly from the source figures
    df["net_profit_margin_pct"] = (df["net_income_musd"] / df["revenue_musd"]) * 100
    df["net_profit_margin_pct"] = df["net_profit_margin_pct"].round(2)

    # 4. Flag negative-equity companies (D/E and ROE not economically meaningful there)
    df["negative_equity"] = (df["debt_to_equity"] < 0).astype(int)

    # 5. Parse period_ending as a real date, extract a numeric year for sorting/plots
    df["period_ending"] = pd.to_datetime(df["period_ending"], errors="coerce")
    df["year"] = df["period_ending"].dt.year

    # 6. Join sector / company name onto every row
    df = df.merge(companies, on="ticker", how="left")

    # 7. Column order + sort
    cols = [
        "ticker", "company_name", "sector", "fiscal_year", "period_ending", "year",
        "revenue_musd", "revenue_growth_pct", "net_income_musd",
        "net_profit_margin_pct", "eps_diluted", "pe_ratio", "debt_to_equity",
        "roe_pct", "negative_equity",
    ]
    df = df[cols].sort_values(["ticker", "period_ending"]).reset_index(drop=True)

    after = len(df)
    print(f"Cleaned dataset: {before} raw rows -> {after} rows (dropped TTM + dupes)")
    print(f"Missing values by column:\n{df.isna().sum()}")

    df.to_csv(OUT_CSV, index=False)
    df.to_sql("financials_clean", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"\nWrote clean dataset to {OUT_CSV} and financials_clean table")


if __name__ == "__main__":
    main()
