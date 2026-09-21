import sys
import os
import shlex
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.tools.databaseserver.databasetools import (
    # GET
    get_part_info,
    get_all_parts,
    get_by_category,
    get_low_stock,
    get_critical_parts,
    get_orders_by_part_number,
    get_orders_by_part_name,
    get_supplier_by_id,
    get_supplier_by_part_name,
    get_supplier_by_part_number,
    get_due_inspections,
    get_part_status,
    # ADD
    add_part,
    add_physical_unit,
    add_order,
    # UPDATE
    update_part,
    update_physical_specs,
    update_supplier,
    update_status,
    update_location,
    update_assigned_to,
    update_inspection,
    update_usage_cycles,
    update_order_status,
    # DELETE
    delete_part,
    delete_physical_unit,
    delete_supplier,
    delete_order,
)
from agent.tools.databaseserver.helper import get_db_connection
def parse_question(question: str):
    q = question.lower().strip()
    parts = shlex.split(question)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # GET patterns (natural language)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if "how many" in q and "do we have" in q:
        item = q.replace("how many", "").replace("do we have", "").replace("?", "").strip()
        return "how_many", item

    elif "where is" in q:
        item = q.replace("where is the", "").replace("where is", "").replace("?", "").strip()
        return "where_is", item

    elif "list all" in q and "in" in q:
        category = q.replace("list all items in", "").replace("?", "").strip()
        return "list_category", category

    elif "show all parts" in q or "list all parts" in q:
        return "all_parts", None

    elif "critical parts" in q or "safety critical" in q:
        return "critical_parts", None

    elif "low stock" in q or "running low" in q:
        return "low_stock", None

    elif "due inspection" in q or "overdue" in q:
        return "due_inspections", None

    elif "orders for" in q:
        item = q.replace("orders for", "").replace("?", "").strip()
        return "orders_by_part", item

    elif "supplier for" in q or "who supplies" in q:
        item = q.replace("supplier for", "").replace("who supplies", "").replace("?", "").strip()
        return "supplier_by_part", item

    elif "condition of" in q or "status of" in q:
        item = q.replace("condition of", "").replace("status of", "").replace("the", "").replace("?", "").strip()
        return "part_status", item
    elif q.startswith("supplier id"):
    # supplier id <supplier_id>

        if len(parts) >= 3:
            return "supplier_by_id", parts[2]
        return "invalid", None

    elif q.startswith("orders by number"):
        # orders by number <part_number>

        if len(parts) >= 4:
            return "orders_by_number", parts[3]
        return "invalid", None

    elif q.startswith("supplier by number"):
        # supplier by number <part_number>

        if len(parts) >= 4:
            return "supplier_by_number", parts[3]
        return "invalid", None
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # ADD commands
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif q.startswith("add part"):
        # add part <part_number> <part_name> <category> <description> <manufacturer>

        if len(parts) >= 7:
            return "add_part", parts[2:]
        return "invalid_add_part", None

    elif q.startswith("add unit"):
        # add unit <part_id> <part_number> <car_position> <compatible_with> <condition> <location> <assigned_to> <date_acquired> <next_inspection_due> <max_usage_cycles> <critical_part>

        if len(parts) >= 13:
            return "add_unit", parts[2:]
        return "invalid_add_unit", None

    elif q.startswith("add order"):
        # add order <part_number> <supplier_id> <quantity> <total_cost> <order_date> <category>

        if len(parts) >= 8:
            return "add_order", parts[2:]
        return "invalid_add_order", None

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # UPDATE commands
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif q.startswith("update part"):
        # update part <part_number> <field> <value>

        if len(parts) >= 5:
            return "update_part", parts[2:]
        return "invalid_update", None

    elif q.startswith("update specs"):
        # update specs <part_number> <field> <value>

        if len(parts) >= 5:
            return "update_specs", parts[2:]
        return "invalid_update", None

    elif q.startswith("update supplier"):
        # update supplier <supplier_id> <field> <value>

        if len(parts) >= 5:
            return "update_supplier", parts[2:]
        return "invalid_update", None

    elif q.startswith("update status"):
        # update status <part_id> <condition> <status>

        if len(parts) >= 5:
            return "update_status", parts[2:]
        return "invalid_update", None

    elif q.startswith("update location"):
        # update location <part_id> <location>

        if len(parts) >= 4:
            return "update_location", parts[2:]
        return "invalid_update", None

    elif q.startswith("update assigned"):
        # update assigned <part_id> <assigned_to>

        if len(parts) >= 4:
            return "update_assigned", parts[2:]
        return "invalid_update", None

    elif q.startswith("update inspection"):
        # update inspection <part_id> <last_date> <next_date>

        if len(parts) >= 5:
            return "update_inspection", parts[2:]
        return "invalid_update", None

    elif q.startswith("update cycles"):
        # update cycles <part_id> <cycles>

        if len(parts) >= 4:
            return "update_cycles", parts[2:]
        return "invalid_update", None

    elif q.startswith("update order"):
        # update order <order_id> <status>

        if len(parts) >= 4:
            return "update_order", parts[2:]
        return "invalid_update", None

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # DELETE commands
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif q.startswith("delete part"):

        if len(parts) >= 3:
            return "delete_part", parts[2]
        return "invalid_delete", None

    elif q.startswith("delete unit"):

        if len(parts) >= 3:
            return "delete_unit", parts[2]
        return "invalid_delete", None

    elif q.startswith("delete supplier"):

        if len(parts) >= 3:
            return "delete_supplier", parts[2]
        return "invalid_delete", None

    elif q.startswith("delete order"):

        if len(parts) >= 3:
            return "delete_order", parts[2]
        return "invalid_delete", None

    else:
        return "unknown", None


def handle_question(question: str):
    intent, keyword = parse_question(question)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # GET handlers
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if intent == "how_many":
        result = get_part_info(keyword)
        if result:
            return f"We have {result['quantity']} {result['part_name']} in stock."
        return f"Part '{keyword}' not found."

    elif intent == "where_is":
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.part_name, s.location, s.assigned_to
                FROM STATUS_CONDITION s
                JOIN PART p ON p.part_id = s.part_id
                JOIN CORE_PART_INFO c ON c.part_number = p.part_number
                WHERE LOWER(c.part_name) = ?
            """, (keyword,))
            results = cursor.fetchall()
        if results:
            responses = []
            for r in results:
                responses.append(f"{r['part_name']} is at '{r['location']}' assigned to {r['assigned_to']}.")
            return "\n".join(responses)
        return f"Part '{keyword}' not found."

    elif intent == "list_category":
        results = get_by_category(keyword.title())
        if results:
            lines = [f"  - {r['part_name']} (x{r['quantity']}) [{r['car_position']}]" for r in results]
            return f"Parts in {keyword.title()}:\n" + "\n".join(lines)
        return f"No parts found in category '{keyword}'."

    elif intent == "all_parts":
        results = get_all_parts()
        if results:
            lines = [f"  - {r['part_name']} (x{r['quantity']}) [{r['category']}]" for r in results]
            return "All parts:\n" + "\n".join(lines)
        return "No parts found."

    elif intent == "critical_parts":
        results = get_critical_parts()
        if results:
            lines = [f"  - {r['part_name']} [{r['category']}] next inspection: {r['next_inspection_due']}" for r in results]
            return "Critical parts:\n" + "\n".join(lines)
        return "No critical parts found."

    elif intent == "low_stock":
        results = get_low_stock(2)
        if results:
            lines = [f"  - {r['part_name']} (x{r['quantity']}) [{r['category']}]" for r in results]
            return "Low stock parts:\n" + "\n".join(lines)
        return "No low stock parts."

    elif intent == "due_inspections":
        results = get_due_inspections()
        if results:
            lines = [f"  - {r['part_name']} [{r['part_id']}] overdue since: {r['next_inspection_due']}" for r in results]
            return "Parts overdue for inspection:\n" + "\n".join(lines)
        return "No overdue inspections."

    elif intent == "orders_by_part":
        results = get_orders_by_part_name(keyword)
        if results:
            lines = [f"  - Order #{r['id']} | {r['quantity']} units | {r['total_cost']} EGP | {r['status']}" for r in results]
            return f"Orders for {keyword}:\n" + "\n".join(lines)
        return f"No orders found for '{keyword}'."

    elif intent == "supplier_by_part":
        results = get_supplier_by_part_name(keyword)
        if results:
            lines = [f"  - {r['name']} | {r['email']} | {r['phone_number']}" for r in results]
            return f"Suppliers for {keyword}:\n" + "\n".join(lines)
        return f"No suppliers found for '{keyword}'."

    elif intent == "part_status":
        results = get_part_status(keyword)
        if results:
            lines = [f"  - {r['part_name']} | condition: {r['condition']} | status: {r['status']}" for r in results]
            return f"Status of {keyword}:\n" + "\n".join(lines)
        return f"Part '{keyword}' not found."

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # ADD handlers
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif intent == "supplier_by_id":
        result = get_supplier_by_id(int(keyword))
        if result:
            lines = [f"  - {r['name']} | {r['email']} | {r['phone_number']}" for r in result]
            return f"Supplier:\n" + "\n".join(lines)
        return f"Supplier '{keyword}' not found."

    elif intent == "orders_by_number":
        results = get_orders_by_part_number(keyword)
        if results:
            lines = [f"  - Order #{r['id']} | {r['quantity']} units | {r['total_cost']} EGP | {r['status']}" for r in results]
            return f"Orders for part number {keyword}:\n" + "\n".join(lines)
        return f"No orders found for part number '{keyword}'."

    elif intent == "supplier_by_number":
        results = get_supplier_by_part_number(keyword)
        if results:
            lines = [f"  - {r['name']} | {r['email']} | {r['phone_number']}" for r in results]
            return f"Suppliers for part number {keyword}:\n" + "\n".join(lines)
        return f"No suppliers found for part number '{keyword}'."

    elif intent == "add_part":
        p = keyword
        result = add_part(p[0], p[1], p[2], p[3], p[4],
                          float(p[5]), p[6], p[7], p[8],
                          int(p[9]), float(p[10]), int(p[11]), bool(int(p[12])))
        return f"Part added: {result}"

    elif intent == "add_unit":
        p = keyword
        result = add_physical_unit(p[0], p[1], p[2], p[3], p[4],
                                   p[5], p[6], p[7], p[8],
                                   int(p[9]), bool(int(p[10])))
        return f"Unit added: {result}"

    elif intent == "add_order":
        p = keyword
        result = add_order(p[0], int(p[1]), int(p[2]),
                           float(p[3]), p[4], p[5])
        return f"Order added: {result}"

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # UPDATE handlers
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif intent == "update_part":
        p = keyword
        result = update_part(p[0], p[1], " ".join(p[2:]))
        return f"Part updated: {result}"

    elif intent == "update_specs":
        p = keyword
        result = update_physical_specs(p[0], p[1], " ".join(p[2:]))
        return f"Specs updated: {result}"

    elif intent == "update_supplier":
        p = keyword
        result = update_supplier(int(p[0]), p[1], " ".join(p[2:]))
        return f"Supplier updated: {result}"

    elif intent == "update_status":
        p = keyword
        result = update_status(p[0], p[1], " ".join(p[2:]))
        return f"Status updated: {result}"

    elif intent == "update_location":
        p = keyword
        result = update_location(p[0], p[1])
        return f"Location updated: {result}"

    elif intent == "update_assigned":
        p = keyword
        result = update_assigned_to(p[0], " ".join(p[1:]))
        return f"Assignment updated: {result}"

    elif intent == "update_inspection":
        p = keyword
        result = update_inspection(p[0], p[1], p[2])
        return f"Inspection updated: {result}"

    elif intent == "update_cycles":
        p = keyword
        result = update_usage_cycles(p[0], int(p[1]))
        return f"Usage cycles updated: {result}"

    elif intent == "update_order":
        p = keyword
        result = update_order_status(int(p[0]), p[1])
        return f"Order status updated: {result}"

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # DELETE handlers
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif intent == "delete_part":
        confirm = input(f"Are you sure you want to delete part '{keyword}'? (yes/no): ")
        if confirm.lower() == "yes":
            result = delete_part(keyword)
            return f"Part deleted: {result}"
        return "Delete cancelled."

    elif intent == "delete_unit":
        confirm = input(f"Are you sure you want to delete unit '{keyword}'? (yes/no): ")
        if confirm.lower() == "yes":
            result = delete_physical_unit(keyword)
            return f"Unit deleted: {result}"
        return "Delete cancelled."

    elif intent == "delete_supplier":
        confirm = input(f"Are you sure you want to delete supplier '{keyword}'? (yes/no): ")
        if confirm.lower() == "yes":
            result = delete_supplier(int(keyword))
            return f"Supplier deleted: {result}"
        return "Delete cancelled."

    elif intent == "delete_order":
        confirm = input(f"Are you sure you want to delete order '{keyword}'? (yes/no): ")
        if confirm.lower() == "yes":
            result = delete_order(int(keyword))
            return f"Order deleted: {result}"
        return "Delete cancelled."

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Invalid / Unknown
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif "invalid" in intent:
        return (f"Invalid command format. Usage:\n"
                f"  add part <part_number> <part_name> <category> <description> <manufacturer> <weight_kg> <material> <dimensions> <color> <supplier_id> <unit_cost> <lead_time_days> <critical_part>\n"
                f"  add unit <part_id> <part_number> <car_position> <compatible_with> <condition> <location> <assigned_to> <date_acquired> <next_inspection_due> <max_usage_cycles> <critical_part>\n"
                f"  add order <part_number> <supplier_id> <quantity> <total_cost> <order_date> <category>\n"
                f"  update part <part_number> <field> <value>\n"
                f"  update specs <part_number> <field> <value>\n"
                f"  update supplier <supplier_id> <field> <value>\n"
                f"  update status <part_id> <condition> <status>\n"
                f"  update location <part_id> <location>\n"
                f"  update assigned <part_id> <assigned_to>\n"
                f"  update inspection <part_id> <last_date> <next_date>\n"
                f"  update cycles <part_id> <cycles>\n"
                f"  update order <order_id> <status>\n"
                f"  delete part <part_number>\n"
                f"  delete unit <part_id>\n"
                f"  delete supplier <supplier_id>\n"
                f"  delete order <order_id>")

    else:
        return ("Sorry I didn't understand. Try:\n"
                "  - How many [item] do we have?\n"
                "  - Where is the [item]?\n"
                "  - List all items in [category]\n"
                "  - Show all parts\n"
                "  - Critical parts\n"
                "  - Low stock\n"
                "  - Due inspections\n"
                "  - Orders for [item]\n"
                "  - Supplier for [item]\n"
                "  - Status of [item]\n"
                "  - add/update/delete commands")
