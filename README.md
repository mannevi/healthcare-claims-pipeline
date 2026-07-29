# 🏥 Healthcare Claims Analytics Pipeline

> End-to-end data pipeline processing **58,066 real Medicare claims**
> through a medallion architecture — GCS bronze → dbt transformation → BigQuery → Looker Studio,
> plus an AI-powered natural language analyst layer on top.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Transformations-FF694B?logo=dbt&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-Data%20Warehouse-4285F4?logo=googlebigquery&logoColor=white)
![GCS](https://img.shields.io/badge/GCS-Data%20Lake-FBBC04?logo=googlecloud&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-Orchestration-017CEE?logo=apacheairflow&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-AI%20Analyst-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-LLM-4285F4?logo=googlegemini&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

**🔗 Live AI Analyst App:** [https://healthcare-claims-ai.streamlit.app/](https://healthcare-claims-ai.streamlit.app/)

---

## 📋 Project Overview

A production-style healthcare data pipeline built around the same problem US payers like CVS Health, Aetna, and UnitedHealth Group solve daily — making raw claims data analytics-ready, then letting anyone query it in plain English.

| | |
|---|---|
| 📦 **Raw Data** | 58,066 Medicare inpatient claims — CMS public dataset |
| ☁️ **Bronze Layer** | Google Cloud Storage — raw CSV untouched |
| 🔧 **Transformation** | dbt — staging, intermediate, and mart layers |
| 🏗️ **Warehouse** | BigQuery — 3 mart tables feeding both a dashboard and an AI assistant |
| 🎛️ **Orchestration** | Apache Airflow — daily DAG |
| 📊 **Dashboard** | Looker Studio — connected to BigQuery mart tables |
| 🤖 **AI Layer** | Natural language → SQL assistant, with safety guardrails, deployed on Streamlit |

---

## 🎯 Business Problem

Healthcare payers process millions of claims daily but struggle to answer basic questions:
- Which states have the highest claim volumes?
- Which diagnoses cost the most?
- Which providers are charging significantly above average?

This pipeline answers all of them — either through the dashboard, or by just asking in plain English.

### Key Findings

| Insight | Value |
|---------|-------|
| Total Medicare spend | **$119.58M** across 19,957 unique claims |
| Average cost per claim | **$5,991.72** |
| Highest claim state | **Florida** |
| Cost trend | Consistent upward trend 2015 → 2022 |

---

## 🤖 AI Analyst Layer

On top of the dbt marts, this project includes a natural-language analyst tool: ask a question in plain English, and it generates SQL, validates it, runs it against BigQuery, and returns real results — no SQL knowledge required.

**Try it live:** [https://healthcare-claims-ai.streamlit.app/](https://healthcare-claims-ai.streamlit.app/)

**How it works**
1. **Schema grounding** — the LLM is only shown the 3 approved mart tables and their real column names, so it can't hallucinate tables that don't exist
2. **SQL generation** — Google Gemini (free tier) generates a SELECT query from the question
3. **Guardrails** — before anything runs, the query is checked against a dangerous-keyword blocklist, a table whitelist, and a row limit — tested against real adversarial prompts (e.g. asking it to generate a DELETE), which it correctly blocked
4. **Execution** — the query runs through a **read-only** BigQuery service account (`BigQuery Data Viewer` role only), so even in a worst case, nothing can be written or deleted
5. **Result** — the answer, the SQL used, and the raw result table are all shown, so it's never a black box

**Tech:** Python, Google Gemini API, BigQuery Python client, Streamlit, deployed on Streamlit Community Cloud

---

## 🛠️ Tech Stack

| Tool | Role |
|------|------|
| **Python 3.11** | Ingestion scripts + AI layer |
| **Google Cloud Storage** | Bronze layer — raw data landing zone |
| **BigQuery** | Data warehouse — raw + analytics datasets |
| **dbt Core** | SQL transformation — staging, intermediate, marts |
| **Apache Airflow** | Pipeline orchestration |
| **Looker Studio** | Business dashboard connected to mart tables |
| **Google Gemini** | LLM powering the natural language SQL assistant |
| **Streamlit** | Web interface for the AI analyst, deployed publicly |

---

## 🏗️ Architecture

```
CMS Claims CSV + ICD-10 Codes
          ↓
    Python Ingestion
          ↓
   GCS Bronze Layer
          ↓
  BigQuery RAW Dataset
          ↓
       dbt Run
  ┌─────────────────────────────┐
  │  staging → intermediate     │
  │  → marts (3 tables)         │
  └─────────────────────────────┘
          ↓
  BigQuery Analytics Dataset
      ↓                ↓
Looker Studio     AI Analyst (Streamlit)
```

---

## 📁 Project Structure

```
healthcare-claims-pipeline/
├── ingestion/
│   ├── extract.py                 ← reads claims CSV + ICD-10 from URL
│   └── upload_to_gcs.py           ← uploads both files to GCS bronze zone
├── transform/
│   └── quality_checks.py          ← file-level pipeline quality checks
├── healthcare_dbt/
│   ├── seeds/
│   │   └── state_codes.csv        ← state code → state name lookup
│   └── models/
│       ├── staging/                ← stg_claims, stg_icd_codes
│       ├── intermediate/           ← int_claims_deduplicated
│       └── marts/                  ← mart_claims_summary, mart_provider_performance, mart_diagnosis_cost_analysis
├── nl_sql_analyst/
│   ├── src/
│   │   ├── app.py                 ← Streamlit UI
│   │   ├── schema_context.py      ← grounds the LLM in the real mart schema
│   │   ├── nl_to_sql_gemini.py    ← generates + validates + executes SQL
│   │   ├── guardrails.py          ← safety checks before any query runs
│   │   └── execute_query.py       ← read-only BigQuery execution
│   └── requirements.txt
├── airflow/
│   └── dags/claims_pipeline_dag.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🌐 Data Sources

| Source | Detail |
|--------|--------|
| **CMS Medicare Claims** | data.cms.gov — pipe-separated CSV — 58,066 rows · 197 columns |
| **ICD-10 Reference** | github.com/k4m1113/ICD-10-CSV — 71,704 codes pulled live via URL |

---

## 🐛 Data Quality Fixes

Found and fixed while validating output through the AI analyst layer — traced from symptom to root cause across the pipeline:

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Diagnosis descriptions always blank | Raw ICD-10 ingestion script was dropping the actual code column, keeping only description + category | Corrected column parsing in ingestion, reloaded raw table, updated staging model |
| Inconsistent claim details for multi-line claims | Deduplication had no tiebreaker when a claim had multiple service lines on the same date, so a random line got kept | Added `claim_line_num` to staging, made deduplication deterministic (always keeps line 1) |
| State shown as a numeric code, not a name | The dbt pipeline never carried over the state-code mapping that existed in an earlier version of the project | Added the mapping as a dbt seed, joined into the relevant marts |

---

## ▶️ How to Run

### Prerequisites
- GCP account with BigQuery + GCS APIs enabled
- Service account key saved as `gcp-key.json` in project root
- Python 3.11
- A free Google Gemini API key (for the AI layer)

### Run the data pipeline

```bash
git clone https://github.com/mannevi/healthcare-claims-pipeline.git
cd healthcare-claims-pipeline

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python ingestion/upload_to_gcs.py

cd healthcare_dbt
dbt seed
dbt run
dbt test
```

### Run the AI analyst locally

```bash
cd nl_sql_analyst/src
pip install -r requirements.txt
set GEMINI_API_KEY=your-key-here
streamlit run app.py
```

---

## 🧠 What I Built and Learned

| Challenge | Solution |
|-----------|----------|
| 197 columns in raw CMS data | Selected the business-relevant columns in dbt staging |
| Duplicate claims from multi-line records | Deterministic deduplication with `ROW_NUMBER()` + a real tiebreaker |
| LLM-generated SQL isn't inherently safe | Built a guardrail layer — keyword blocklist, table whitelist, read-only credentials — and tested it against real adversarial prompts |
| Free-tier LLM models get deprecated fast | Learned to check for current model names rather than hardcoding one, and to separate dev-tier models from production-tier ones |
| Bad data reaching the warehouse | dbt tests + file-level Python checks |
| Credentials security | Service account keys and Streamlit secrets kept out of git entirely |

---

## 🚀 Future Improvements

- [ ] Add incremental dbt models instead of full refresh on every run
- [ ] Add RAG over the ICD-10 reference table for semantic diagnosis search
- [ ] Close the Airflow DAG gap where `icd_codes_raw` isn't auto-reloaded

---

## 👩‍💻 Author

**Manne Vaishnavi**
MS in Computer Science

[![GitHub](https://img.shields.io/badge/GitHub-mannevi-181717?logo=github)](https://github.com/mannevi)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-vaishnavimanne-0A66C2?logo=linkedin)](https://www.linkedin.com/in/vaishnavimanne/)

---

*Built with real CMS Medicare data — no mock datasets.*
