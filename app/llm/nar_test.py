from app.analysis.root_cause import find_root_cause
from app.llm.narration import build_prompt

finding = find_root_cause(year=2018, month_a=5, month_b=6)
prompt = build_prompt(finding)
print(prompt)
print("---LENGTH---")
print(len(prompt))