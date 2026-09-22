import sys
sys.path.insert(0, r'C:\Users\hashe\Desktop\curt')
from phase1.assistant_phase1 import handle_question

# Hard test scenario - real texts like list Brake Caliper (BRK-C-001) with no / or , separators
# Each must NOT return Sorry I didn't understand
hard_cases = [
    "list Brake Caliper (BRK-C-001)",
    "list brake caliper",
    "list BRK-C-001",
    "show brake caliper details",
    "give me info on BRK-C-001",
    "get Brake Caliper",
    "How many brake caliper do we have",
    "How many brak caliper do we have",
    "Where is brake caliper",
    "where is BRK-C-001",
    "List all items in Brakes",
    "show all parts",
    "delete Brake Caliper",
    "delete unit PRT-003",
    "remove front left",
    "remove Brake Disc",
    "add new Brake Disc (Front Left)",
    "list brake disc",
    "show me the brake caliper",
    "give details for brake caliper",
    "critical parts",
    "low stock",
    "due inspections",
    "orders for Brake Caliper",
    "supplier for Brake Caliper",
    "status of Brake Caliper",
]

failed = []
for q in hard_cases:
    res = handle_question(q)
    if "Sorry I didn't understand" in res:
        failed.append(q)
        print(f"FAIL {q!r} -> {res[:120]}")
    else:
        print(f"PASS {q!r:40} -> {res[:80].replace(chr(10),' | ')}")

if failed:
    print(f"\n{len(failed)} failed out of {len(hard_cases)}")
    sys.exit(1)
else:
    print(f"\nAll {len(hard_cases)} hard cases passed - Phase 1 immune")
