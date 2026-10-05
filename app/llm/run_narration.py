import json
from app.analysis.root_cause import find_root_cause
from app.llm.narration import narrate_finding

finding = find_root_cause(year=2018, month_a=5, month_b=6)
result = narrate_finding(finding)
print(json.dumps(result, indent=2,ensure_ascii=False))