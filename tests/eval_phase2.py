"""Evaluation Q14 — 20 Q/A accuracy for Phase2 (judged via Phase1 ground truth)."""
import sys
sys.path.insert(0, '.')
from phase1.assistant_phase1 import handle_question
# 20 eval prompts covering spec Q types
prompts = [
("How many brake calipers do we have?", "2"),
("Where is the ECU?", "Car"),
("List all items in Brakes", "BRK-C-001"),
("Show all parts", "Brake Caliper"),
("Critical parts", "critical"),
("Low stock", "Low stock"),
("Due inspections", "overdue"),
("Orders for brake caliper", "Order"),
("Supplier for engine", "Honda"),
("Status of monocoque", "condition"),
("How many front wing assembly do we have?", "2"),
("Where is the engine?", "Car"),
("List all suppliers", "Brembo"),
("Where is BRK-C-001", "Car"),
("How many rim set do we have?", "2"),
("List all items in Aero", "WNG-F-001"),
("What about BRK-C-001", "BRK-C-001"),
("brak caliper", "Did you mean"),
("how many do we have", "Which item"),
("where is brk-c-001", "Car"),
]
passed=0
for q, expected in prompts:
    r=handle_question(q)
    ok = expected.lower() in r.lower() and "Sorry" not in r
    print(f"{'PASS' if ok else 'FAIL'} {q!r:35} -> {r[:80].replace(chr(10),'|')}")
    if ok: passed+=1
print(f"\n{passed}/{len(prompts)} eval passed")
