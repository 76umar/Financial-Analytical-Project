"""
Stage 4: Interactive Streamlit dashboard.

Run locally:
    pip install -r requirements.txt
    streamlit run dashboard/app.py

Deploy: push this repo to GitHub, then deploy for free on Streamlit
Community Cloud (https://streamlit.io/cloud), pointing it at
dashboard/app.py. See README.md for full deployment steps.
"""

import os
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "financials.db")

SECTOR_COLORS = {
    "Software": "#0072B2",
    "Semiconductors": "#E69F00",
    "Hardware": "#009E73",
    "Internet & Cloud": "#CC79A7",
    "IT Services": "#D55E00",
    "Cybersecurity": "#56B4E9",
}

st.set_page_config(
    page_title="IT Sector Financial Health Tracker",
    page_icon="\U0001F4CA",
    layout="wide",
)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM financials_clean", conn, parse_dates=["period_ending"]
    )
    conn.close()
    df["fiscal_year_end"] = df["period_ending"].dt.year
    return df


df = load_data()

# ---------------------------------------------------------------- Sidebar --
st.sidebar.title("Filters")

sectors = sorted(df["sector"].unique())
selected_sectors = st.sidebar.multiselect("Sector", sectors, default=sectors)

filtered_by_sector = df[df["sector"].isin(selected_sectors)]
companies_in_scope = sorted(
    filtered_by_sector[["ticker", "company_name"]]
    .drop_duplicates()
    .apply(lambda r: f"{r['ticker']} — {r['company_name']}", axis=1)
)

default_company = companies_in_scope[0] if companies_in_scope else None
selected_company_label = st.sidebar.selectbox(
    "Company (for the detail view)", companies_in_scope, index=0 if default_company else None
)
selected_ticker = selected_company_label.split(" — ")[0] if selected_company_label else None

year_min, year_max = int(df["fiscal_year_end"].min()), int(df["fiscal_year_end"].max())
year_range = st.sidebar.slider(
    "Fiscal year range", min_value=year_min, max_value=year_max,
    value=(year_min, year_max),
)

scope = filtered_by_sector[
    (filtered_by_sector["fiscal_year_end"] >= year_range[0])
    & (filtered_by_sector["fiscal_year_end"] <= year_range[1])
]

# ------------------------------------------------------------------ Title --
st.title("\U0001F4CA IT-Industry Financial Health Tracker")
st.caption(
    "Revenue growth, profitability and leverage across 30 publicly listed "
    "IT-industry companies — Software, Semiconductors, Hardware, Internet & "
    "Cloud, IT Services and Cybersecurity. Source: stockanalysis.com, accessed 2026-09-08."
)

# --------------------------------------------------------- KPI summary row --
if selected_ticker:
    company_rows = df[df["ticker"] == selected_ticker].sort_values("period_ending")
    latest = company_rows.iloc[-1]
    prior = company_rows.iloc[-2] if len(company_rows) > 1 else None

    st.subheader(f"{latest['company_name']} ({selected_ticker}) — {latest['fiscal_year']}")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(
        "Revenue",
        f"${latest['revenue_musd'] / 1000:,.1f}B",
        f"{latest['revenue_growth_pct']:+.1f}%" if pd.notna(latest["revenue_growth_pct"]) else None,
    )
    k2.metric(
        "Net Profit Margin",
        f"{latest['net_profit_margin_pct']:.1f}%" if pd.notna(latest["net_profit_margin_pct"]) else "N/A",
    )
    k3.metric(
        "ROE",
        f"{latest['roe_pct']:.1f}%" if pd.notna(latest["roe_pct"]) else "N/A",
    )
    k4.metric(
        "Debt / Equity",
        f"{latest['debt_to_equity']:.2f}" if pd.notna(latest["debt_to_equity"]) else "N/A",
    )
    k5.metric(
        "P/E Ratio",
        f"{latest['pe_ratio']:.1f}" if pd.notna(latest["pe_ratio"]) else "N/A",
    )

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        fig_rev = px.bar(
            company_rows, x="fiscal_year", y="revenue_musd",
            title=f"{selected_ticker} Revenue by Fiscal Year ($M)",
            color_discrete_sequence=[SECTOR_COLORS.get(latest["sector"], "#0072B2")],
        )
        fig_rev.update_layout(xaxis_title="", yaxis_title="Revenue ($M)")
        st.plotly_chart(fig_rev, use_container_width=True)
    with c2:
        fig_eps = px.line(
            company_rows, x="fiscal_year", y="eps_diluted", markers=True,
            title=f"{selected_ticker} Diluted EPS by Fiscal Year",
            color_discrete_sequence=[SECTOR_COLORS.get(latest["sector"], "#0072B2")],
        )
        fig_eps.update_layout(xaxis_title="", yaxis_title="EPS ($)")
        st.plotly_chart(fig_eps, use_container_width=True)

st.divider()

# --------------------------------------------------------- Sector overview --
st.subheader("Sector Comparison (fiscal years in range, all selected sectors)")

latest_per_ticker = scope.sort_values("period_ending").groupby("ticker").tail(1)

c3, c4 = st.columns(2)
with c3:
    sector_margin = (
        latest_per_ticker.groupby("sector")["net_profit_margin_pct"].mean().sort_values()
    )
    fig_margin = px.bar(
        sector_margin, orientation="h",
        title="Average Net Profit Margin by Sector",
        labels={"value": "Net Profit Margin (%)", "sector": ""},
        color=sector_margin.index,
        color_discrete_map=SECTOR_COLORS,
    )
    fig_margin.update_layout(showlegend=False)
    st.plotly_chart(fig_margin, use_container_width=True)

with c4:
    fig_scatter = px.scatter(
        latest_per_ticker[latest_per_ticker["negative_equity"] == 0],
        x="debt_to_equity", y="roe_pct", color="sector", text="ticker",
        title="ROE vs. Debt-to-Equity (latest fiscal year, by company)",
        color_discrete_map=SECTOR_COLORS,
        labels={"debt_to_equity": "Debt / Equity", "roe_pct": "ROE (%)"},
    )
    fig_scatter.update_traces(textposition="top center", marker=dict(size=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------- Ratio heatmap --
st.subheader("Ratio Heatmap — Latest Fiscal Year, All Companies in Scope")

heatmap_df = latest_per_ticker.set_index("ticker")[
    ["revenue_growth_pct", "net_profit_margin_pct", "roe_pct", "debt_to_equity", "pe_ratio"]
].rename(columns={
    "revenue_growth_pct": "Revenue Growth %",
    "net_profit_margin_pct": "Net Margin %",
    "roe_pct": "ROE %",
    "debt_to_equity": "Debt/Equity",
    "pe_ratio": "P/E",
})

fig_heat = go.Figure(
    data=go.Heatmap(
        z=heatmap_df.T.values,
        x=heatmap_df.index,
        y=heatmap_df.columns,
        colorscale="RdYlGn",
        zmid=0,
        hoverongaps=False,
    )
)
fig_heat.update_layout(height=350, margin=dict(t=10, b=10))
st.plotly_chart(fig_heat, use_container_width=True)

# ------------------------------------------------------------------ Table --
with st.expander("Show underlying data table"):
    st.dataframe(
        scope[[
            "ticker", "company_name", "sector", "fiscal_year", "revenue_musd",
            "revenue_growth_pct", "net_profit_margin_pct", "roe_pct",
            "debt_to_equity", "eps_diluted", "pe_ratio",
        ]].sort_values(["sector", "ticker", "fiscal_year"]),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Built with Python, pandas, SQLite and Streamlit. "
    "Data: company financial statements via stockanalysis.com. "
    "This dashboard is for educational purposes only and is not investment advice."
)
