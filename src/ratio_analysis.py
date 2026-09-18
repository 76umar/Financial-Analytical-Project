"""
Stage 3: Financial ratio analysis, sector leaders, and static charts.

Reads the cleaned dataset and:
  1. Prints top-3 healthiest companies per sector (reuses the SQL health score).
  2. Generates 4 static charts into charts/ as PNGs:
       - revenue_trend.png        (revenue over time, top companies by sector)
       - margin_comparison.png    (net profit margin by sector, bar chart)
       - roe_vs_de_scatter.png    (ROE vs debt-to-equity scatter, most recent year)
       - eps_growth_leaders.png   (top 10 EPS growth, most recent full year vs prior)
"""

import os
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "financials.db")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

# Colorblind-friendly categorical palette (Okabe-Ito), used consistently
# across every chart / the dashboard for the 6 sectors.
SECTOR_COLORS = {
    "Software": "#0072B2",
    "Semiconductors": "#E69F00",
    "Hardware": "#009E73",
    "Internet & Cloud": "#CC79A7",
    "IT Services": "#D55E00",
    "Cybersecurity": "#56B4E9",
}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#444444",
    "axes.grid": True,
    "grid.color": "#e6e6e6",
    "grid.linewidth": 0.8,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM financials_clean", conn, parse_dates=["period_ending"])
    conn.close()
    return df


def latest_per_company(df):
    return df.sort_values("period_ending").groupby("ticker").tail(1)


def chart_revenue_trend(df):
    # One representative (largest by latest revenue) company per sector, trended over time
    latest = latest_per_company(df)
    leaders = latest.sort_values("revenue_musd", ascending=False).groupby("sector").head(1)["ticker"]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for ticker in leaders:
        sub = df[df["ticker"] == ticker].sort_values("period_ending")
        sector = sub["sector"].iloc[0]
        ax.plot(sub["period_ending"], sub["revenue_musd"] / 1000, marker="o",
                label=f"{ticker} ({sector})", color=SECTOR_COLORS.get(sector))

    ax.set_title("Revenue Trend — Largest Company per Sector", fontsize=13, fontweight="bold")
    ax.set_ylabel("Revenue ($ billions)")
    ax.set_xlabel("Fiscal Year End")
    ax.legend(fontsize=8, loc="upper left")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f B"))
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "revenue_trend.png"), dpi=150)
    plt.close(fig)


def chart_margin_comparison(df):
    latest = latest_per_company(df)
    sector_margin = latest.groupby("sector")["net_profit_margin_pct"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [SECTOR_COLORS.get(s) for s in sector_margin.index]
    ax.barh(sector_margin.index, sector_margin.values, color=colors)
    ax.set_title("Average Net Profit Margin by Sector (Latest Fiscal Year)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Net Profit Margin (%)")
    for i, v in enumerate(sector_margin.values):
        ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "margin_comparison.png"), dpi=150)
    plt.close(fig)


def chart_roe_vs_de(df):
    latest = latest_per_company(df)
    latest = latest[latest["negative_equity"] == 0].dropna(subset=["roe_pct", "debt_to_equity"])
    latest = latest[latest["roe_pct"].between(-50, 200)]  # trim extreme outliers for readability

    fig, ax = plt.subplots(figsize=(8.5, 6))
    for sector, sub in latest.groupby("sector"):
        ax.scatter(sub["debt_to_equity"], sub["roe_pct"], label=sector,
                   color=SECTOR_COLORS.get(sector), s=70, alpha=0.85, edgecolor="white")
        for _, row in sub.iterrows():
            ax.annotate(row["ticker"], (row["debt_to_equity"], row["roe_pct"]),
                        fontsize=7, xytext=(4, 3), textcoords="offset points")

    ax.set_title("Return on Equity vs. Debt-to-Equity (Latest Fiscal Year)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Debt-to-Equity Ratio")
    ax.set_ylabel("Return on Equity (%)")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "roe_vs_de_scatter.png"), dpi=150)
    plt.close(fig)


def chart_eps_growth_leaders(df):
    # EPS growth = (latest full FY eps - prior FY eps) / |prior FY eps|
    rows = []
    for ticker, sub in df.groupby("ticker"):
        sub = sub.sort_values("period_ending")
        if len(sub) < 2:
            continue
        prior, latest = sub.iloc[-2], sub.iloc[-1]
        if prior["eps_diluted"] in (0, None) or pd.isna(prior["eps_diluted"]):
            continue
        growth = (latest["eps_diluted"] - prior["eps_diluted"]) / abs(prior["eps_diluted"]) * 100
        rows.append((ticker, latest["sector"], growth))

    growth_df = pd.DataFrame(rows, columns=["ticker", "sector", "eps_growth_pct"])
    top10 = growth_df.reindex(growth_df["eps_growth_pct"].abs().sort_values(ascending=False).index).head(10)
    top10 = top10.sort_values("eps_growth_pct")

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    colors = [SECTOR_COLORS.get(s) for s in top10["sector"]]
    ax.barh(top10["ticker"], top10["eps_growth_pct"], color=colors)
    ax.axvline(0, color="#444444", linewidth=0.8)
    ax.set_title("Largest YoY EPS Swings (Most Recent Full Fiscal Year)", fontsize=13, fontweight="bold")
    ax.set_xlabel("EPS Growth (%)")
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "eps_growth_leaders.png"), dpi=150)
    plt.close(fig)


def print_sector_leaders(df):
    conn = sqlite3.connect(DB_PATH)
    q = open(os.path.join(BASE_DIR, "sql", "analysis_queries.sql")).read()
    q3 = q.split("-- Q3.")[1].split("-- Q4.")[0]
    q3 = "-- Q3." + q3
    res = pd.read_sql_query(q3, conn)
    print("Top 3 healthiest companies per sector:\n", res.to_string(index=False))
    conn.close()


def main():
    os.makedirs(CHARTS_DIR, exist_ok=True)
    df = load()
    chart_revenue_trend(df)
    chart_margin_comparison(df)
    chart_roe_vs_de(df)
    chart_eps_growth_leaders(df)
    print_sector_leaders(df)
    print(f"\nCharts written to {CHARTS_DIR}/")


if __name__ == "__main__":
    main()
