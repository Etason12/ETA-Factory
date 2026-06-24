"""
Migration: create procurement flow tables and seed initial inventory from stock_quantity.
Run: python migrations/add_procurement_flow.py
"""

import os
import sys
import sqlite3


def run_migration(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Suppliers
    c.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(200),
            phone VARCHAR(20),
            email VARCHAR(120),
            address TEXT,
            payment_terms VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_deleted BOOLEAN NOT NULL DEFAULT 0,
            deleted_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
            created_by_id INTEGER REFERENCES users(id),
            updated_by_id INTEGER REFERENCES users(id)
        )
    """)

    # 2. Purchase Orders
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number VARCHAR(50) NOT NULL UNIQUE,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            order_date DATE NOT NULL DEFAULT (date('now')),
            expected_date DATE,
            status VARCHAR(30) NOT NULL DEFAULT 'Draft',
            notes TEXT,
            approved_by_id INTEGER REFERENCES users(id),
            approved_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
            created_by_id INTEGER REFERENCES users(id),
            updated_by_id INTEGER REFERENCES users(id)
        )
    """)

    # 3. Purchase Order Items
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
            raw_material_id INTEGER NOT NULL REFERENCES raw_materials(id),
            quantity_ordered NUMERIC(12,2) NOT NULL,
            unit_cost NUMERIC(12,2) NOT NULL,
            quantity_received NUMERIC(12,2) NOT NULL DEFAULT 0
        )
    """)

    # 4. Raw Material Inventory (per warehouse)
    c.execute("""
        CREATE TABLE IF NOT EXISTS raw_material_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_material_id INTEGER NOT NULL REFERENCES raw_materials(id),
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            quantity_on_hand NUMERIC(12,2) NOT NULL DEFAULT 0,
            reserved_quantity NUMERIC(12,2) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
            created_by_id INTEGER REFERENCES users(id),
            updated_by_id INTEGER REFERENCES users(id),
            UNIQUE(raw_material_id, warehouse_id)
        )
    """)

    # 5. Raw Material Ledger
    c.execute("""
        CREATE TABLE IF NOT EXISTS raw_material_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_material_id INTEGER NOT NULL REFERENCES raw_materials(id),
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            movement_type VARCHAR(50) NOT NULL,
            quantity NUMERIC(12,2) NOT NULL,
            unit_cost NUMERIC(12,2),
            reference_type VARCHAR(50),
            reference_id INTEGER,
            transaction_date DATETIME NOT NULL DEFAULT (datetime('now')),
            created_by_id INTEGER REFERENCES users(id)
        )
    """)

    # 6. Store Requisitions
    c.execute("""
        CREATE TABLE IF NOT EXISTS store_requisitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requisition_number VARCHAR(50) NOT NULL UNIQUE,
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            production_batch_id INTEGER REFERENCES production_batches(id),
            requisition_date DATE NOT NULL DEFAULT (date('now')),
            status VARCHAR(30) NOT NULL DEFAULT 'Pending',
            notes TEXT,
            approved_by_id INTEGER REFERENCES users(id),
            approved_at DATETIME,
            issued_by_id INTEGER REFERENCES users(id),
            issued_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
            created_by_id INTEGER REFERENCES users(id),
            updated_by_id INTEGER REFERENCES users(id)
        )
    """)

    # 7. Store Requisition Items
    c.execute("""
        CREATE TABLE IF NOT EXISTS store_requisition_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_requisition_id INTEGER NOT NULL REFERENCES store_requisitions(id),
            raw_material_id INTEGER NOT NULL REFERENCES raw_materials(id),
            quantity_requested NUMERIC(12,2) NOT NULL,
            quantity_issued NUMERIC(12,2) NOT NULL DEFAULT 0
        )
    """)

    # Seed RawMaterialInventory from existing stock_quantity if no inventory exists
    existing = c.execute("SELECT COUNT(*) FROM raw_material_inventory").fetchone()[0]
    if existing == 0:
        rows = c.execute("""
            SELECT rm.id, rm.stock_quantity, w.id
            FROM raw_materials rm
            CROSS JOIN (SELECT id FROM warehouses LIMIT 1) w
            WHERE rm.stock_quantity > 0 AND rm.is_deleted = 0
        """).fetchall()
        for rm_id, qty, w_id in rows:
            c.execute("""
                INSERT INTO raw_material_inventory (raw_material_id, warehouse_id, quantity_on_hand)
                VALUES (?, ?, ?)
            """, (rm_id, qty, w_id))
            c.execute("""
                INSERT INTO raw_material_ledger (raw_material_id, warehouse_id, movement_type, quantity, unit_cost)
                SELECT ?, ?, 'Opening Balance', ?, cost_price FROM raw_materials WHERE id = ?
            """, (rm_id, w_id, qty, rm_id))
        print(f"Seeded {len(rows)} raw materials into inventory")
    else:
        print("RawMaterialInventory already populated, skipping seed")

    conn.commit()
    conn.close()
    print("Migration completed successfully")


if __name__ == '__main__':
    # Determine DB path
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_db = os.path.join(script_dir, 'src', 'instance', 'eta_dev.db')
    alt_db = os.path.join(script_dir, 'instance', 'eta_dev.db')

    for db_path in [default_db, alt_db]:
        if os.path.exists(db_path):
            print(f"Migrating: {db_path}")
            run_migration(db_path)
            break
    else:
        print("No database found, creating new from models. Run flask first to create DB.")
