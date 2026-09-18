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

## Planned Enhancements
- Order count / AOV decomposition (distinguish demand vs. pricing effects)
- Year-over-year comparison support
- Explicit surfacing of offsetting/opposite-direction movers in findings
- Natural-language query layer: map free-text questions ("why did sales drop 
  on X date", "show me electronics revenue") to a fixed set of safe, 
  pre-defined query intents + extracted parameters (category, date range). 
  LLM maps text -> structured intent only; it never decides what analysis 
  to run or interprets causality itself — that logic stays in deterministic 
  code, preserving the core "LLM narrates, never reasons" principle.