import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helper import (
    mcp,
    get_db_connection,
    _fetch_parts,
    _fetch_status,
    _fetch_orders,
    _fetch_suppliers,
    _insert_lifecycle_tracking,
    _insert_status_condition,
    _insert_part,
    _insert_part_supplier,
    _insert_physical_specs,
    _insert_core_part_info,
    _update_table,
    _delete_from
)
# ─────────────────────────────────────
# GET functions
# ─────────────────────────────────────
@mcp.tool()
def get_by_part_number(part_number: str):
    """Use for lookup by part_number (e.g., BRK-C-001, WNG-F-001). Returns quantity, category, car_position."""
    return _fetch_parts("c.part_number", part_number)

@mcp.tool()
def get_by_name(part_name: str):
    """Use for general part lookup by name (e.g., brake caliper, front wing). For 'where is' location queries use get_part_status instead."""
    return _fetch_parts("c.part_name", part_name)

@mcp.tool()
def get_by_category(category: str):
    """Use for 'list all items in <category>' queries (Aero, Brakes, Suspension, etc.). Returns part_id (PRT-003), part_number (BRK-C-001), part_name, quantity total per model, car_position (Front Left/Right). Quantity 2 for BRK-C-001 means 1 Front Left + 1 Front Right, not 2 each."""
    return _fetch_parts("c.category", category)

@mcp.tool()
def get_part_status(part_name: str):
    """Use for 'where is' and location queries. Returns location, assigned_to, condition, status for a part by name."""
    return _fetch_status('c.part_name', part_name)


@mcp.tool()
def get_orders_by_part_number(part_number: str):
    """Get all orders for a part by part number"""
    return _fetch_orders("o.part_number", part_number)

@mcp.tool()
def get_orders_by_part_name(part_name: str):
    """Get all orders for a part by part name"""
    return _fetch_orders("c.part_name", part_name)
@mcp.tool()
def get_supplier_by_id(supplier_id: int):
    """Get supplier info by supplier ID"""
    return _fetch_suppliers("s.id", supplier_id)

@mcp.tool()
def get_supplier_by_part_name(part_name: str):
    """Get supplier info by part name"""
    return _fetch_suppliers("c.part_name", part_name)

@mcp.tool()
def get_supplier_by_part_number(part_number: str):
    """Get supplier info by part number"""
    return _fetch_suppliers("c.part_number", part_number)

@mcp.tool()
def get_all_parts_name():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT part_name FROM CORE_PART_INFO;")
        return [row["part_name"] for row in cursor.fetchall()]

@mcp.tool()
def get_part_info(part_name: str):
    """Use for 'how many' quantity queries. Handles singular/plural (e.g., brake calipers -> brake caliper)."""
    singular = part_name[:-1] if part_name.lower().endswith('s') else part_name
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT part_number, part_name, quantity, category
            FROM CORE_PART_INFO
            WHERE LOWER(part_name) IN (LOWER(?), LOWER(?))
        """, (part_name, singular))
        row = cursor.fetchone()
        return dict(row) if row else None

@mcp.tool()
def get_all_parts():
    """Use for 'show all parts' or 'list all parts'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT part_number, part_name, quantity, category
            FROM CORE_PART_INFO
            ORDER BY part_name
        """)
        return [dict(row) for row in cursor.fetchall()]

@mcp.tool()
def get_due_inspections():
    """Get all parts that are overdue for inspection"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.part_number,
                c.part_name,
                c.category,
                p.part_id,
                p.car_position,
                lt.last_inspection_date,
                lt.next_inspection_due,
                lt.critical_part
            FROM LIFECYCLE_TRACKING lt
            JOIN PART p ON p.part_id = lt.part_id
            JOIN CORE_PART_INFO c ON c.part_number = p.part_number
            WHERE lt.next_inspection_due < DATE('now')
            ORDER BY lt.next_inspection_due ASC
        """)
        return [dict(row) for row in cursor.fetchall()]


@mcp.tool()
def flag_shortage(item_name: str, threshold: int = 2):
    """Flag low stock for a single item. Logs LOW STOCK FLAG if quantity < threshold. Use for 'low stock' single-item checks per spec."""
    info = get_part_info(item_name)
    if not info:
        # try close match for typo
        import difflib
        all_names = get_all_parts_name()
        close = difflib.get_close_matches(item_name, all_names, n=1, cutoff=0.5)
        if close:
            info = get_part_info(close[0])
        if not info:
            return {"flagged": False, "error": f"Part '{item_name}' not found"}
    qty = info["quantity"]
    flagged = qty < threshold
    if flagged:
        print(f"LOW STOCK FLAG: {info['part_name']} x{qty} < {threshold}")
    return {"flagged": flagged, "part_name": info["part_name"], "quantity": qty, "threshold": threshold}

@mcp.tool()
def get_low_stock(threshold: int):
    """Get all parts with quantity below the given threshold"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.part_number,
                c.part_name,
                c.quantity,
                c.category
            FROM CORE_PART_INFO AS c
            WHERE c.quantity < ?
        """, (threshold,))
        return [dict(row) for row in cursor.fetchall()]

@mcp.tool()
def get_critical_parts():
    """Get all parts marked as critical (safety)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.part_number,
                c.part_name,
                c.category,
                p.car_position,
                lt.usage_cycles,
                lt.max_usage_cycles,
                lt.next_inspection_due
            FROM LIFECYCLE_TRACKING lt
            JOIN PART p ON p.part_id = lt.part_id
            JOIN CORE_PART_INFO c ON c.part_number = p.part_number
            WHERE lt.critical_part = 1
        """)
        return [dict(row) for row in cursor.fetchall()]
    
@mcp.tool()
def get_all_categories():
    """Get all unique categories currently in the inventory"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category 
            FROM CORE_PART_INFO
            ORDER BY category
        """)
        return [row['category'] for row in cursor.fetchall()]

@mcp.tool()
def get_all_suppliers():
    """Get all unique suppliers with contact info and parts they supply. Use for 'list all suppliers'."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.name, s.contact_name, s.email, s.phone_number, s.website, s.governorate,
                   GROUP_CONCAT(c.part_name || ' (' || c.part_number || ')', ', ') as parts_supplied
            FROM SUPPLIER_INFO s
            LEFT JOIN PART_SUPPLIER ps ON ps.supplier_id = s.id
            LEFT JOIN CORE_PART_INFO c ON c.part_number = ps.part_number
            GROUP BY s.id
            ORDER BY s.name
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        # ensure parts_supplied is list for clarity
        for r in rows:
            if r.get("parts_supplied"):
                r["parts_supplied"] = [p.strip() for p in r["parts_supplied"].split(",")]
            else:
                r["parts_supplied"] = []
        return rows
    
# ─────────────────────────────────────
# ADD functions
# ─────────────────────────────────────

@mcp.tool()
def add_part(part_number: str, part_name: str, category: str,
             description: str, manufacturer: str, weight_kg: float,
             material: str, dimensions: str, color: str,
             supplier_id: int, unit_cost: float,
             lead_time_days: int, preferred: bool):
    """Add a new part model with its physical specs and supplier.
    Valid categories: Aero, Suspension, Brakes, Steering,
    Powertrain, Chassis, Safety, Wheels & Tires, Cooling, Electronics
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        _insert_core_part_info(cursor, part_number, part_name, 
                               category, description, manufacturer)
        _insert_physical_specs(cursor, part_number, weight_kg, 
                               material, dimensions, color)
        _insert_part_supplier(cursor, part_number, supplier_id, 
                              unit_cost, lead_time_days, preferred)
        conn.commit()
        return {"success": True, "part_number": part_number}


@mcp.tool()
def add_physical_unit(part_id: str, part_number: str, car_position: str = "Spare",
                      compatible_with: str = "2024 CURT-01", condition: str = "New", location: str = "Workshop",
                      assigned_to: str = None, date_acquired: str = None,
                      next_inspection_due: str = None, max_usage_cycles: int = 100,
                      critical_part: bool = True):
    """Add a new physical unit — inserts into PART, STATUS_CONDITION
    and LIFECYCLE_TRACKING in one go. Use existing part_number like BRK-D-001 for Brake Disc, generate new unique part_id like PRT-007. Even if a unit with same part_number+car_position exists, this creates an additional physical unit (inventory can have multiple). Valid conditions: New, Used, Damaged, Under Repair
    """
    if date_acquired is None:
        date_acquired = datetime.now().strftime("%Y-%m-%d")
    if next_inspection_due is None:
        next_inspection_due = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        _insert_part(cursor, part_id, part_number, car_position, compatible_with)
        _insert_status_condition(cursor, part_id, condition, location, assigned_to)
        _insert_lifecycle_tracking(cursor, part_id, date_acquired, 
                                   next_inspection_due, max_usage_cycles, critical_part)
        conn.commit()
        return {"success": True, "part_id": part_id}


@mcp.tool()
def add_order(part_number: str, supplier_id: int, quantity: int,
              total_cost: float, order_date: str, category: str):
    """Add a new purchase order.
    Valid categories: Sponsorship, Club Budget, Competition,
    R&D, Maintenance, Donation
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ORDERS 
                (part_number, supplier_id, quantity, total_cost, 
                order_date, category, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        """, (part_number, supplier_id, quantity, total_cost, 
              order_date, category))
        conn.commit()
        return {"success": True, "order_id": cursor.lastrowid}

    
# ─────────────────────────────────────
# UPDATE functions
# ─────────────────────────────────────

@mcp.tool()
def update_location(part_id: str, location: str):
    """Update the location of a physical unit"""
    return _update_table('STATUS_CONDITION', 'location', 
                          location, 'part_id', part_id)

@mcp.tool()
def update_assigned_to(part_id: str, assigned_to: str):
    """Update which car a physical unit is assigned to"""
    return _update_table('STATUS_CONDITION', 'assigned_to', 
                          assigned_to, 'part_id', part_id)

@mcp.tool()
def update_inspection(part_id: str, last_date: str, next_date: str):
    """Update inspection dates for a physical unit.
    Date format: YYYY-MM-DD
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE LIFECYCLE_TRACKING
            SET last_inspection_date = ?, next_inspection_due = ?
            WHERE part_id = ?
        """, (last_date, next_date, part_id))
        conn.commit()
        return {"success": True, "updated": cursor.rowcount}

@mcp.tool()
def update_usage_cycles(part_id: str, cycles: int):
    """Update usage cycles for a physical unit after a race"""
    return _update_table('LIFECYCLE_TRACKING', 'usage_cycles',
                          cycles, 'part_id', part_id)

@mcp.tool()
def update_order_status(order_id: int, status: str):
    """Update the status of an order.
    Valid statuses: Pending, Ordered, Delivered, Cancelled
    """
    allowed_statuses = ['Pending', 'Ordered', 'Delivered', 'Cancelled']
    if status not in allowed_statuses:
        return {"success": False, "error": f"Invalid status. Choose from {allowed_statuses}"}
    return _update_table('ORDERS', 'status', status, 'id', order_id)

_PART_FIELDS = {'part_name', 'category', 'description', 'manufacturer'}
_SPEC_FIELDS = {'weight_kg', 'material', 'dimensions', 'color'}
_SUPPLIER_FIELDS = {'name', 'contact_name', 'email', 'phone_number', 'website', 'governorate'}

@mcp.tool()
def update_part(part_number: str, field: str, value):
    if field not in _PART_FIELDS:
        return {"success": False, "error": f"Invalid field. Choose from {sorted(_PART_FIELDS)}"}
    return _update_table('CORE_PART_INFO', field, value, 'part_number', part_number)

@mcp.tool()
def update_physical_specs(part_number: str, field: str, value):
    if field not in _SPEC_FIELDS:
        return {"success": False, "error": f"Invalid field. Choose from {sorted(_SPEC_FIELDS)}"}
    return _update_table('PHYSICAL_SPECS', field, value, 'part_number', part_number)

@mcp.tool()
def update_supplier(supplier_id: int, field: str, value):
    if field not in _SUPPLIER_FIELDS:
        return {"success": False, "error": f"Invalid field. Choose from {sorted(_SUPPLIER_FIELDS)}"}
    return _update_table('SUPPLIER_INFO', field, value, 'id', supplier_id)

@mcp.tool()
def update_status(part_id: str, condition: str, status: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE STATUS_CONDITION
            SET condition = ?, status = ?
            WHERE part_id = ?
        """, (condition, status, part_id))
        conn.commit()
        return {"success": True, "updated": cursor.rowcount}
# ─────────────────────────────────────
# DELETE functions
# ─────────────────────────────────────

@mcp.tool()
def delete_part(part_number: str):
    """Delete a part model and all related data.
    Cascades to: PART, PHYSICAL_SPECS, PART_SUPPLIER
    and their children STATUS_CONDITION, LIFECYCLE_TRACKING
    """
    return _delete_from('CORE_PART_INFO', 'part_number', part_number)

@mcp.tool()
def delete_physical_unit(part_id: str):
    """Delete a single physical unit by exact part_id like PRT-003, PRT-004, PRT-005, PRT-006 (from get_by_category). Never use invented IDs like BRK-C-FL-001. For Brakes, PRT-003=Front Left Caliper, PRT-004=Front Right Caliper, PRT-005=Front Left Disc, PRT-006=Front Right Disc. Always confirm before deleting.
    Cascades to: STATUS_CONDITION, LIFECYCLE_TRACKING
    """
    return _delete_from('PART', 'part_id', part_id)

@mcp.tool()
def delete_supplier(supplier_id: int):
    """Delete a supplier.
    Cascades to: PART_SUPPLIER
    """
    return _delete_from('SUPPLIER_INFO', 'id', supplier_id)

@mcp.tool()
def delete_order(order_id: int):
    """Delete a purchase order"""
    return _delete_from('ORDERS', 'id', order_id)

# ─────────────────────────────────────
# Entry point
# ─────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")