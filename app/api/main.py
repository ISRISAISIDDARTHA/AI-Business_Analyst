from fastapi import FastAPI, Query
from app.analysis.root_cause import find_root_cause

app = FastAPI(title="AI Business Analyst")

@app.get("/root-cause")
def get_root_cause(
    year: int = Query(..., description="Year to analyze, e.g. 2018"),
    month_a: int = Query(..., ge=1, le=12, description="First month (baseline period)"),
    month_b: int = Query(..., ge=1, le=12, description="Second month (comparison period)"),
    top_n: int = Query(3, description="Number of top movers to return per dimension"),
):
    result = find_root_cause(year=year, month_a=month_a, month_b=month_b, top_n=top_n)
    return result