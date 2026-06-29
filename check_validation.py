import json
from pathlib import Path

REPORT_PATH = Path("reports/latest_report.json")

with open(REPORT_PATH, encoding="utf-8") as f:
    r = json.load(f)

rag = r["rag"]
report = rag["report"]
intel  = rag["intelligence"]

print("=== VALIDATION DEBUG ===\n")
print(f"Report words: {len(report.split())}")
print(f"Opportunities: {len(intel['opportunities'])}")
print(f"Risks: {len(intel['risks'])}")
print(f"Validated: {rag['validated']}\n")

# check what the validator looks for
risk_keywords = [r["title"].lower()[:20] for r in intel.get("risks", [])]
opp_keywords  = [o["title"].lower()[:20] for o in intel.get("opportunities", [])]
report_lower  = report.lower()

print("=== Opportunity keywords (first 20 chars of each title) ===")
for kw in opp_keywords:
    found = kw in report_lower
    print(f"  {'✅' if found else '❌'} '{kw}'")

print("\n=== Risk keywords (first 20 chars of each title) ===")
for kw in risk_keywords:
    found = kw in report_lower
    print(f"  {'✅' if found else '❌'} '{kw}'")

print("\n=== First 300 chars of report ===")
print(report[:300])