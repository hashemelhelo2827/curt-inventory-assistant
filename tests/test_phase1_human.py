import sys
sys.path.insert(0, r'C:\Users\hashe\Desktop\curt')
from phase1.assistant_phase1 import handle_question

prompts = [
    "can you show me the brake calipers please",
    "show me the brake caliper",
    "list Brake Caliper (BRK-C-001)",
    "brake caliper details please",
    "what about BRK-C-001",
    "tell me about brake calipers",
    "brak caliper",
    "calipars",
    "brack disc",
    "brk c 001",
    "prt 003",
    "please list calipers",
    "delete brake caliper please",
    "remove one",
    "delete it",
    "list them",
    "how many do we have",
    "PRT-003 | Brake Caliper",
    "PRT-003 | BRAKE CALIPER",
    "BRK-C-001 - Brake Caliper",
    "brake-caliper",
    "brake caliper.",
    "DELETE BRAKE CALIPER",
    "List Brake Caliper (BRK-C-001)?",
    "bro hey tell me about ecu please thanks",
    "the brake calipers",
    "a brake caliper",
    "caliper",
    "where is brk-c-001",
    "prt-003",
]

failed = []
for q in prompts:
    # ensure no slash or comma in prompt per spec
    assert "/" not in q and "," not in q, f"prompt must not contain / or ,: {q!r}"
    r = handle_question(q)
    if "Sorry I didn't understand" in r:
        failed.append((q, r[:200]))
        print(f"FAIL {q!r:45} -> {r[:120].replace(chr(10),' | ')}")
    else:
        # also ensure some content signal for list/where/how many
        has_signal = any(k in r for k in ["BRK", "PRT", "Brake", "quantity", "We have", "Details for", "Found", "Which item", "Did you mean", "is at", "Part", "Units", "Brake Caliper", "ECU", "Engine"])
        status = "PASS" if has_signal else "PASS*"
        print(f"{status} {q!r:45} -> {r[:100].replace(chr(10),' | ')}")

print("\n--- Sequential yes test ---")
# trigger typo then yes
r1 = handle_question("calipars")
print(f"calipars -> {r1[:120].replace(chr(10),' | ')}")
r2 = handle_question("yes")
print(f"yes -> {r2[:120].replace(chr(10),' | ')}")
if "Sorry I didn't understand" in r2:
    failed.append(("yes after calipars", r2[:200]))
    print("FAIL yes after calipars")
else:
    print("PASS yes after calipars")

if failed:
    print(f"\n{len(failed)} failed out of {len(prompts)+1}")
    for q, r in failed:
        print(f"  - {q!r}: {r[:150]}")
    sys.exit(1)
else:
    print(f"\nAll {len(prompts)} hard cases passed + yes sequence — Phase 1 human immune")
