-- =========================================================================
-- Stage 2: SQL Analysis Queries
-- Run against data/processed/financials.db (table: financials_clean)
-- Answers the business questions from the project brief using
-- SELECT, GROUP BY, JOIN, HAVING and subqueries.
-- =========================================================================

-- Q1. Which sector has the best average net profit margin (most recent
--     fiscal year available per company)?
WITH latest AS (
    SELECT f.*, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY period_ending DESC) rn
    FROM financials_clean f
)
SELECT sector,
       ROUND(AVG(net_profit_margin_pct), 2) AS avg_net_margin_pct,
       COUNT(*) AS n_companies
FROM latest
WHERE rn = 1
GROUP BY sector
ORDER BY avg_net_margin_pct DESC;

-- Q2. Which company has the most consistent revenue growth (lowest
--     standard deviation of YoY revenue growth %, min 4 years of data)?
SELECT ticker, company_name, sector,
       ROUND(AVG(revenue_growth_pct), 2)  AS avg_growth_pct,
       ROUND(
         SQRT(AVG(revenue_growth_pct * revenue_growth_pct) - AVG(revenue_growth_pct) * AVG(revenue_growth_pct)),
         2
       ) AS stddev_growth_pct,
       COUNT(*) AS n_years
FROM financials_clean
GROUP BY ticker
HAVING COUNT(*) >= 4
ORDER BY stddev_growth_pct ASC
LIMIT 10;

-- Q3. Top 3 most financially healthy companies per sector, by a simple
--     composite score (avg ROE + avg net margin - avg debt/equity*10),
--     using only the most recent fiscal year and excluding negative-equity
--     companies from the D/E component.
WITH latest AS (
    SELECT f.*, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY period_ending DESC) rn
    FROM financials_clean f
),
scored AS (
    SELECT ticker, company_name, sector,
           roe_pct, net_profit_margin_pct, debt_to_equity,
           ROUND(
             COALESCE(roe_pct, 0)
             + COALESCE(net_profit_margin_pct, 0)
             - COALESCE(CASE WHEN negative_equity = 0 THEN debt_to_equity END, 0) * 10,
             2
           ) AS health_score
    FROM latest
    WHERE rn = 1
),
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY sector ORDER BY health_score DESC) AS sector_rank
    FROM scored
)
SELECT sector, sector_rank, ticker, company_name, health_score, roe_pct, net_profit_margin_pct, debt_to_equity
FROM ranked
WHERE sector_rank <= 3
ORDER BY sector, sector_rank;

-- Q4. Sector-level average P/E ratio (valuation), most recent year, only
--     where P/E is meaningful (positive earnings).
WITH latest AS (
    SELECT f.*, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY period_ending DESC) rn
    FROM financials_clean f
)
SELECT sector,
       ROUND(AVG(pe_ratio), 2) AS avg_pe_ratio,
       COUNT(pe_ratio) AS n_with_pe
FROM latest
WHERE rn = 1 AND pe_ratio IS NOT NULL AND pe_ratio < 200  -- exclude extreme low-earnings outliers
GROUP BY sector
ORDER BY avg_pe_ratio ASC;

-- Q5. Companies whose revenue grew every single year in the dataset
--     (subquery: no year with negative growth).
SELECT DISTINCT ticker, company_name, sector
FROM financials_clean fc
WHERE ticker NOT IN (
    SELECT ticker FROM financials_clean WHERE revenue_growth_pct < 0
)
ORDER BY sector, ticker;

-- Q6. Join example: companies + their latest-year EPS and revenue,
--     ranked within sector by revenue (JOIN + window function).
SELECT c.sector, c.ticker, c.company_name,
       f.fiscal_year, f.revenue_musd, f.eps_diluted,
       RANK() OVER (PARTITION BY c.sector ORDER BY f.revenue_musd DESC) AS revenue_rank_in_sector
FROM companies c
JOIN financials_clean f ON f.ticker = c.ticker
WHERE (f.ticker, f.period_ending) IN (
    SELECT ticker, MAX(period_ending) FROM financials_clean GROUP BY ticker
)
ORDER BY c.sector, revenue_rank_in_sector;

-- Q7. Average debt-to-equity by sector, excluding structurally
--     negative-equity companies (HAVING to only show sectors with 3+ data points).
SELECT sector,
       ROUND(AVG(debt_to_equity), 2) AS avg_debt_to_equity,
       COUNT(*) AS n
FROM financials_clean
WHERE negative_equity = 0 AND debt_to_equity IS NOT NULL
GROUP BY sector
HAVING COUNT(*) >= 3
ORDER BY avg_debt_to_equity ASC;
