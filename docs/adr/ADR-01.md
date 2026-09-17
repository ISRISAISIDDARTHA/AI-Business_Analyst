# ADR-001: Local Postgres for Dev

Decision: Postgres in Docker, local, not Snowflake — for now
Why: small dataset (~100k rows, Snowflake's scaling features irrelevant here), 
$0 budget (Snowflake trial expires, needs credit card), 
project needs to survive being offline/restarted for 4 months without depending on a live paid service
Revisit: Snowflake as stretch goal later, dbt makes migration low-cost