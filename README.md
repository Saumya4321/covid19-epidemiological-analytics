
# COVID-19 Surveillance Analytics & Regional Risk Assessment — India

An end-to-end data analytics project on India's COVID-19 pandemic data, covering
data engineering, epidemiological ratio analysis, time series decomposition,
regression analysis, and geospatial visualization — built around real
government data with all its inconsistencies, gaps, and quirks.

**Live dashboard:** https://covid19-epidemiological-analytics.streamlit.app/

---

## Overview

This project works with three public datasets on India's COVID-19 pandemic —
daily case counts, statewise testing details, and statewise vaccination
records — sourced from the Ministry of Health & Family Welfare and
covid19india.org. Rather than treating this as a clean, ready-to-model
dataset, the project deliberately surfaces and documents the real data
quality issues involved in working with multi-source government data:
misspelled state names, inconsistent date formats, administrative boundary
changes mid-timeline, and reporting artifacts.

## Data Sources

- `covid_19_india.csv` — daily case-level data (confirmed, cured, deaths) per state
- `StatewiseTestingDetails.csv` — daily testing volume and positivity data per state
- `covid_vaccine_statewise.csv` — daily vaccination rollout data per state

All three span different but overlapping windows between January 2020 and
August 2021.


## Tech Stack

Python (pandas, numpy) · statsmodels · geopandas · Docker · Streamlit

---

## 1. Data Engineering

Cleaned and merged all three datasets on `(State, Date)` into a single
analysis-ready table.

**Issues found and resolved:**
- **State name inconsistencies**: misspellings (`Telengana`, `Karanataka`,
  `Himanchal Pradesh`), footnote artifacts (`Bihar****`, `Maharashtra***`),
  and a 2020 union territory merger (`Daman & Diu` + `Dadra and Nagar Haveli`
  → `Dadra and Nagar Haveli and Daman and Diu`) reflected inconsistently
  across the three files.
- **Non-state placeholder rows** (`Unassigned`, `Cases being reassigned to
  states`) removed from the case data.
- **Column name whitespace** (`' Sites '` instead of `'Sites'`) and a
  **`pd.NA` vs `np.nan` dtype-corruption bug** that silently converted a
  clean numeric column to `object` dtype mid-analysis.

## 2. Epidemiological Ratios

Computed four standard ratios per state, per day:

| Ratio | Formula |
|---|---|
| Growth Rate | `(Cases_t − Cases_t-1) / Cases_t-1` |
| Test Positivity Rate | `Positive / TotalSamples` |
| Case Fatality Ratio (CFR) | `Deaths / Confirmed` |
| Recovery Rate | `Cured / Confirmed` |

Ratios were computed **per state** using
`groupby('State')` before any `.diff()` or `.shift()` operation; a naive
ungrouped diff would silently compute nonsense values across state
boundaries.

#### Results
| Ratio | Average  | Median | Maximum |
|---|---| --- | --- |
| Growth Rate | 3.1% | 0.6% | 14% |
| Test Positivity Rate | 4.4% | 3.17% | 21.9% |
| Case Fatality Ratio (CFR) | 1.3% | 1.2% | 50% |
| Recovery Rate | 77.3% | 89.2% | 100% |


## 3. Time Series Analysis

**Trend decomposition** (`statsmodels.tsa.seasonal_decompose`, additive
model, weekly period) on the national daily new-case series:

<img width="1200" height="800" alt="trend_decomposition" src="https://github.com/user-attachments/assets/551b8277-c6ba-4c96-82e2-90c278d82494" />


- **Trend**: clearly captures both of India's major waves; the first
  peaking ~September 2020 (~90K/day) and the much larger Delta wave peaking
  ~April–May 2021 (~400K/day).
- **Weekly seasonality**: a strong, consistent pattern throughout the full
  timeline. The sharpest dip
  is  **Tuesday** (-7,028 below trend), with Thursday–Sunday
  consistently elevated. This points to a reporting lag concentrated early in
  the week rather than simple weekend under-reporting.
- Tested `model='multiplicative'` as an alternative; it failed outright,
  since multiplicative decomposition can't handle the 34 days with exactly
  zero reported cases in the dataset (mostly legitimate early-pandemic days,
  plus one confirmed data collection gap on 2021-03-11 where every state
  simultaneously shows zero new cases).

**Regression 1 — Vaccination Rate vs. Growth Rate**: coefficient = +0.054
(p < 0.001), R² = 0.167. Vaccination rate is *positively* associated with
growth rate, which is the opposite of the intuitive hypothesis. Very likely
cause of confusion: the vaccination-data window (Jan–Jun 2021) overlaps almost
entirely with the Delta wave, so this regression cannot separate
"vaccination causing growth" from "both driven by the same wave." 

**Regression 2 — Confirmed vs. Cured cases**: R² = 0.995, coefficient =
0.95. For every 1 additional confirmed case (nationally, cumulative), ~0.95 additional cured cases follow.
Near perfect linear fit. This is because a large majority of confirmed cases eventually resolve to cured within the dataset's timeframe.

## 4. Geospatial Analysis

Built choropleth maps using India state boundary shapefiles
([geohacker/india](https://github.com/geohacker/india)), which required
resolving several real boundary-matching issues:

- Simple renames (`Orissa` → `Odisha`, `Uttaranchal` → `Uttarakhand`)
- Dissolving two separate shapefile polygons into one to match the 2020
  Dadra & Nagar Haveli / Daman & Diu merger
- **Telangana and Ladakh have no boundaries in this shapefile** — verified
  (not assumed) by reprojecting to a metric CRS and comparing polygon area
  against real-world figures, confirming the shapefile predates both the
  2014 Telangana split and the 2019 Ladakh split. Resolved by aggregating
  data back to the old combined boundaries (Telangana → Andhra Pradesh,
  Ladakh → Jammu and Kashmir) rather than dropping these states from the map
  entirely — a documented limitation, since the map can't visually
  distinguish these pairs.

#### Peak Test Positivity Rate
<img width="1200" height="1440" alt="choropleth_peak_positivity" src="https://github.com/user-attachments/assets/744c368c-3a6e-4d78-ad67-e91fe0a438a3" />
Result: 33 of 34 states rendered with data; Lakshadweep has no positivity data in the source dataset. Maharashtra (20.7%) and Andhra Pradesh (22.0%, includes aggregated Telangana data) show the highest peak positivity, consistent with widely reported accounts of these states being among the hardest-hit during the pandemic, particularly the 2021 Delta wave. Note: Andhra Pradesh's figure reflects the combined AP+Telangana region due to the shapefile boundary limitation

#### Total Confirmed Cases
<img width="1200" height="1440" alt="choropleth_total_confirmed" src="https://github.com/user-attachments/assets/7665aa1d-8b49-44b6-8046-72c4109354ee" />
Result: Maharastra dominant (~6.35M), consistent with the 1st map and widely reported case burden data.


#### Case Fatality Rate
than Maharashtra, showing that 
<img width="1200" height="1440" alt="choropleth_cfr" src="https://github.com/user-attachments/assets/d83d9dc4-185b-4cf4-a092-e318942ae218" />
Result: Though Maharastra had the most number of confirmed cases, Punjab has the highest CFR (2.72%). This shows that case burden and fatality risk aren't the same
signal.

#### Vaccination Coverage Rate 
<img width="1200" height="1440" alt="choropleth_vaccination_rate" src="https://github.com/user-attachments/assets/89655bc3-48dc-45ae-bd71-0b811468e837" />
Result: Dominated by small-population UTs — Lakshadweep (65%), Dadra and Nagar Haveli and Daman and Diu (52%), Sikkim (~50%). This is a real, well-documented pattern (smaller populations reach high per-capita coverage 
faster with less logistical complexity)

## 5. Interactive Dashboard

Built with Streamlit, two pages:
- **Overview** — national KPIs, daily case trend, weekly reporting pattern chart
- **Risk Analysis (Maps)** — switchable choropleth across all four metrics above, with underlying data table

Live at: https://covid19-epidemiological-analytics.streamlit.app/

---




## Running Locally

```bash
git clone <repo-url>
cd <repo-folder>/dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Limitations

- Vaccination data only covers Jan 16 – Jun 24, 2021, limiting any
  vaccination-related analysis to that window.
- The geospatial choropleths cannot distinguish Telangana from Andhra
  Pradesh, or Ladakh from Jammu and Kashmir, due to the source shapefile
  predating both administrative splits (see Section 4).
