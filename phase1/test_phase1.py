test_questions = [
    # ─────────────────────────────────────
    # GET — natural language
    # ─────────────────────────────────────
    "How many brake calipers do we have?",
    "How many front wing assembly do we have?",
    "How many engine do we have?",
    "How many rim set do we have?",

    "Where is the ECU?",
    "Where is the engine?",
    "Where is the steering rack?",
    "Where is the monocoque?",

    "List all items in Aero",
    "List all items in Brakes",
    "List all items in Suspension",
    "List all items in Electronics",

    "Show all parts",
    "Critical parts",
    "Low stock",
    "Due inspections",

    "Orders for brake caliper",
    "Orders for engine",

    "Supplier for engine",
    "Supplier for front wing assembly",

    "Status of monocoque",
    "Status of ECU",
    "Condition of brake disc",

    "orders by number WNG-F-001",
    "orders by number BRK-C-001",

    "supplier by number WNG-F-001",
    "supplier by number PWR-E-001",

    "supplier id 1",
    "supplier id 3",

    # ─────────────────────────────────────
    # ADD commands
    # ─────────────────────────────────────
    "add part COL-D-001 \"Cooling Duct\" Cooling \"Duct for radiator\" In-house 0.5 \"Carbon Fiber\" 300x200x100mm Black 1 150.00 7 0",
    "add order WNG-F-001 1 2 500.00 2024-09-01 Sponsorship",

    # ─────────────────────────────────────
    # UPDATE commands
    # ─────────────────────────────────────
    "update part WNG-F-001 description Updated carbon fiber front wing",
    "update specs BRK-C-001 color Silver",
    "update supplier 1 email newcontact@brembo.com",
    "update status PRT-001 Used In Use",
    "update location PRT-002 Workshop",
    "update assigned PRT-003 2025 CURT-02",
    "update inspection PRT-004 2024-09-01 2024-12-01",
    "update cycles PRT-005 25",
    "update order 1 Delivered",

    # ─────────────────────────────────────
    # DELETE commands
    # ─────────────────────────────────────
    "delete order 10",

    # ─────────────────────────────────────
    # Invalid / Unknown
    # ─────────────────────────────────────
    "add part",
    "update part",
    "delete",
    "what is the best part?",
    "hello",
]