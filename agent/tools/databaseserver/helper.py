import sqlite3
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),  # current file location
    '..', '..', '..',           # go up to curt/
    'database',
    'curt_inventory.db'
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

mcp = FastMCP("Database Manager")



# ─────────────────────────────────────
# GET functions
# ─────────────────────────────────────

def _fetch_parts(where_clause: str, value: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                p.part_id, 
                c.part_number,
                c.part_name,
                c.quantity,
                c.category,
                c.description,
                c.manufacturer,
                p.car_position,
                p.compatible_with
            FROM CORE_PART_INFO AS c
            JOIN PART AS p ON c.part_number = p.part_number
            WHERE LOWER({where_clause}) = LOWER(?)
        """, (value,))
        return [dict(row) for row in cursor.fetchall()]
def _fetch_all_parts():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.part_id,
                c.part_number,
                c.part_name,
                c.quantity,
                c.category,
                c.description,
                c.manufacturer,
                p.car_position,
                p.compatible_with
            FROM CORE_PART_INFO AS c
            JOIN PART AS p
                ON c.part_number = p.part_number
        """)
        return [dict(row) for row in cursor.fetchall()]
    
def _fetch_status(where_clause: str, value: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                c.part_name,
                s.condition,
                s.status,
                s.location,
                s.assigned_to
            FROM STATUS_CONDITION AS s
            JOIN PART AS p ON s.part_id = p.part_id
            JOIN CORE_PART_INFO AS c ON p.part_number = c.part_number
            WHERE LOWER({where_clause}) = LOWER(?)
        """, (value,))
        return [dict(row) for row in cursor.fetchall()]

def _fetch_orders(where_clause: str, value: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                o.id,
                o.part_number,
                c.part_name,
                s.name AS supplier_name,
                o.quantity,
                o.total_cost,
                o.order_date,
                o.category,
                o.status
            FROM ORDERS o
            JOIN CORE_PART_INFO c ON c.part_number = o.part_number
            JOIN SUPPLIER_INFO s ON s.id = o.supplier_id
            WHERE LOWER({where_clause}) = LOWER(?)
        """, (value,))
        return [dict(row) for row in cursor.fetchall()]

def _fetch_suppliers(where_clause: str, value: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                s.id,
                s.name,
                s.contact_name,
                s.email,
                s.phone_number,
                s.website,
                s.governorate,
                ps.unit_cost,
                ps.lead_time_days,
                ps.preferred,
                c.part_name,
                c.part_number
            FROM SUPPLIER_INFO s
            JOIN PART_SUPPLIER ps ON ps.supplier_id = s.id
            JOIN CORE_PART_INFO c ON c.part_number = ps.part_number
            WHERE LOWER({where_clause}) = LOWER(?)
        """, (value,))
        return [dict(row) for row in cursor.fetchall()]

# ─────────────────────────────────────
# ADD functions
# ─────────────────────────────────────

def _insert_part(cursor, part_id: str, part_number: str, 
                 car_position: str, compatible_with: str):
    cursor.execute("""
        INSERT INTO PART (part_id, part_number, car_position, compatible_with)
        VALUES (?, ?, ?, ?)
    """, (part_id, part_number, car_position, compatible_with))

def _insert_status_condition(cursor, part_id: str, condition: str,
                              location: str, assigned_to: str):
    cursor.execute("""
        INSERT INTO STATUS_CONDITION (part_id, condition, status, location, assigned_to)
        VALUES (?, ?, 'Available', ?, ?)
    """, (part_id, condition, location, assigned_to))

def _insert_lifecycle_tracking(cursor, part_id: str, date_acquired: str,
                                next_inspection_due: str, max_usage_cycles: int,
                                critical_part: bool):
    cursor.execute("""
        INSERT INTO LIFECYCLE_TRACKING 
            (part_id, date_acquired, last_inspection_date,
            next_inspection_due, usage_cycles, max_usage_cycles, critical_part)
        VALUES (?, ?, DATE('now'), ?, 0, ?, ?)
    """, (part_id, date_acquired, next_inspection_due, max_usage_cycles, critical_part))
def _insert_core_part_info(cursor, part_number: str, part_name: str,
                            category: str, description: str, manufacturer: str):
    cursor.execute("""
        INSERT INTO CORE_PART_INFO 
            (part_number, part_name, category, description, manufacturer)
        VALUES (?, ?, ?, ?, ?)
    """, (part_number, part_name, category, description, manufacturer))

def _insert_physical_specs(cursor, part_number: str, weight_kg: float,
                            material: str, dimensions: str, color: str):
    cursor.execute("""
        INSERT INTO PHYSICAL_SPECS 
            (part_number, weight_kg, material, dimensions, color)
        VALUES (?, ?, ?, ?, ?)
    """, (part_number, weight_kg, material, dimensions, color))

def _insert_part_supplier(cursor, part_number: str, supplier_id: int,
                           unit_cost: float, lead_time_days: int, preferred: bool):
    cursor.execute("""
        INSERT INTO PART_SUPPLIER 
            (part_number, supplier_id, unit_cost, lead_time_days, preferred)
        VALUES (?, ?, ?, ?, ?)
    """, (part_number, supplier_id, unit_cost, lead_time_days, preferred))

# ─────────────────────────────────────
# UPDATE functions
# ─────────────────────────────────────

def _update_table(table: str, field: str, value, 
                  where_field: str, where_value):
    """Internal helper for single field updates"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {table}
            SET {field} = ?
            WHERE {where_field} = ?
        """, (value, where_value))
        conn.commit()
        return {"success": True, "updated": cursor.rowcount}

# ─────────────────────────────────────
# DELETE functions
# ─────────────────────────────────────
def _delete_from(table: str, where_field: str, where_value):
    """Internal helper for delete operations"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            DELETE FROM {table}
            WHERE {where_field} = ?
        """, (where_value,))
        conn.commit()
        return {"success": True, "deleted": cursor.rowcount}