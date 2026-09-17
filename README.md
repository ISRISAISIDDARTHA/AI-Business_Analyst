# AI Business Analyst

Ingests multi-source business data through real ETL into a data warehouse,
and uses a local LLM to narrate deterministic root-cause findings — not a
dashboard, not a "chat with your data" wrapper.

**Core principle:** the LLM never reasons about causality. Root cause is
computed first via statistical analysis; the LLM only narrates the
precomputed, verified finding.

## Setup
1. Copy `.env.example` to `.env` and fill in values
2. `docker compose up -d`
3. `pip install -r requirements.txt`
4. `python -m app.ingestion.load_raw_to_postgres`

## Data
Raw Olist dataset not included in repo (see `.gitignore`). Download from
[Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and
extract into `data/raw/`.