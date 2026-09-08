# 📊 IT-Industry Financial Health Tracker

Financial health analysis and interactive dashboard for **30 publicly listed
IT-industry companies** across six sub-sectors — Software, Semiconductors,
Hardware, Internet & Cloud, IT Services, and Cybersecurity.

**Live dashboard:** _add your Streamlit Community Cloud link here after deploying (see [Deployment](#deployment))_

> 📸 Add a real screenshot/GIF of the running dashboard here once you've deployed it — run `streamlit run dashboard/app.py`, take a screenshot, save it as `docs/dashboard.png`, and add `![Dashboard](docs/dashboard.png)` above this line.

## Motivation

Financial ratio analysis — profit margins, return on equity, leverage, and
valuation — is the foundation of how analysts compare companies and sectors.
This project takes that analysis end-to-end: from raw company financials, through
a relational database and SQL queries, to an interactive dashboard anyone can
use to explore 30 IT companies without touching a spreadsheet. It answers a
simple business question: **which parts of the IT industry are financially
healthiest right now, and why?**

## Tech Stack

| Tool | Why |
|---|---|
| **Python + pandas** | Data cleaning, ratio calculations, transformation |
| **SQLite + SQL** | Relational storage; `GROUP BY`, `JOIN`, `HAVING`, window functions, subqueries to answer business questions |
| **Jupyter Notebook** | Documents the analysis and thought process end-to-end |
| **matplotlib** | Static charts for the written analysis |
| **Plotly + Streamlit** | Interactive dashboard — filters, KPI cards, heatmap — deployable for free |
| **Git / GitHub** | Version control and project showcase |

## Project Structure

```
.
├── data/
│   ├── raw/                    # Source data + the script that builds it
│   │   ├── build_raw_dataset.py
│   │   ├── raw_financials.csv
│   │   └── companies.csv
│   └── processed/               # SQLite DB + cleaned CSV (generated)
│       ├── financials.db
│       └── financials_clean.csv
├── src/
│   ├── load_to_sqlite.py        # Stage 1: raw CSV -> SQLite
│   ├── clean_data.py            # Stage 2: pandas cleaning
│   └── ratio_analysis.py        # Stage 3: ratios + static charts
├── sql/
│   └── analysis_queries.sql     # Stage 2: business-question SQL queries
├── charts/                      # Generated static PNG charts
├── notebooks/
│   └── 01_analysis.ipynb        # Full documented analysis walkthrough
├── dashboard/
│   └── app.py                   # Stage 4: Streamlit dashboard
├── requirements.txt
└── README.md
```

## How to Run It Locally

```bash
# 1. Clone the repo
git clone https://github.com/76umar/Financial-Analytical-Project.git
cd Financial-Analytical-Project

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Rebuild the data pipeline (raw CSV -> SQLite -> cleaned data -> charts)
python3 data/raw/build_raw_dataset.py
python3 src/load_to_sqlite.py
python3 src/clean_data.py
python3 src/ratio_analysis.py

# 4. Explore the analysis notebook
jupyter notebook notebooks/01_analysis.ipynb

# 5. Launch the interactive dashboard
streamlit run dashboard/app.py
```

The database and charts are already generated and committed, so you can skip
straight to steps 4–5 if you just want to explore.

## Deployment

Deploy the dashboard for free on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push this repo to your own GitHub account (already done if you're reading this on GitHub).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and click **New app**.
3. Select this repo, branch `main`, and set the main file path to `dashboard/app.py`.
4. Click **Deploy**. You'll get a public URL — add it to the top of this README.

## Key Findings

- **Internet & Cloud and Semiconductors post the highest net margins** — Alphabet and Meta both clear 30% net margin, and AI-driven demand pushed NVIDIA's margin above 55% in its latest fiscal year, well ahead of every other company in the dataset.
- **Software's high average debt-to-equity is mostly a buyback artifact, not distress** — Oracle's ratio (3.89x) looks alarming next to peers like Microsoft (0.29x) or ServiceNow (0.19x), but stems from aggressive share buybacks shrinking the equity base rather than excessive borrowing.
- **Cybersecurity is the growth-over-profitability sector** — CrowdStrike, Palo Alto Networks, and Fortinet all post strong, consistent double-digit revenue growth, but only Fortinet has settled into consistent GAAP profitability.
- **Apple stands alone on capital efficiency** — ROE of 148–175% across the last five fiscal years, unmatched by any other hardware company in the set.
- **IT services (Accenture, Cognizant, Infosys) are the steadiest performers** — mid-single to low-double-digit revenue growth, low debt, and ROE in the 15–32% range every year, without the volatility seen in semiconductors or cybersecurity.

Full analysis and methodology: [`notebooks/01_analysis.ipynb`](notebooks/01_analysis.ipynb).

## Future Improvements

- ML-based revenue forecasting per company (e.g. simple trend or Prophet model)
- Automated data refresh via a live financial data API
- Quarterly (not just annual) granularity
- Layer in stock price history to compute realised total shareholder return

## Data Sources

Company financial statements and ratios sourced from [stockanalysis.com](https://stockanalysis.com),
accessed 2026-09-08. Figures are as originally reported by each company (SAP
reports in EUR millions; all other companies in USD millions). This project
and its dashboard are for educational purposes only and do not constitute
investment advice.

## Companies Covered

<details>
<summary>30 companies across 6 sectors (click to expand)</summary>

| Sector | Companies |
|---|---|
| **Software** | Microsoft, Oracle, Salesforce, Adobe, Intuit, ServiceNow, SAP, Workday |
| **Semiconductors** | NVIDIA, Broadcom, Intel, AMD, Qualcomm, Texas Instruments, Micron |
| **Hardware** | Apple, Cisco, Dell, HP Inc., Hewlett Packard Enterprise |
| **Internet & Cloud** | Alphabet, Meta Platforms |
| **IT Services** | IBM, Accenture, Cognizant, Infosys, DXC Technology |
| **Cybersecurity** | Palo Alto Networks, CrowdStrike, Fortinet |

</details>
