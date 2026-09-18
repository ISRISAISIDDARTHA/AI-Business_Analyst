from app.analysis.root_cause import find_root_cause
import json

result = find_root_cause(year=2018, month_a=5, month_b=6)
print(json.dumps(result, indent=2, default=str))