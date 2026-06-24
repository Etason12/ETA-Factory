"""
Migration: Add raw_materials table, update bom_items, drop product_type/is_produced from products.
Run: python backend/migrations/add_raw_materials_bom_cost.py
"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'instance', 'eta_dev.db')
print('Target DB:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

def add_column(table, column, col_type):
    try:
        cur.execute('ALTER TABLE "{}" ADD COLUMN "{}" {}'.format(table, column, col_type))
        print('  Added {}.{} ({})'.format(table, column, col_type))
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print('  {}.{} already exists'.format(table, column))
        else:
            raise

print('1. Adding bom_labor_cost and bom_utility_cost to products...')
add_column('products', 'bom_labor_cost', 'NUMERIC(12,2) DEFAULT 0')
add_column('products', 'bom_utility_cost', 'NUMERIC(12,2) DEFAULT 0')

print('2. Creating raw_materials table...')
cur.execute('''
    CREATE TABLE IF NOT EXISTS raw_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku VARCHAR(50) NOT NULL UNIQUE,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        cost_price NUMERIC(12,2) DEFAULT 0,
        unit_id INTEGER NOT NULL REFERENCES units(id),
        is_active BOOLEAN NOT NULL DEFAULT 1,
        min_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0,
        max_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0,
        stock_quantity NUMERIC(12,2) NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by_id INTEGER REFERENCES users(id),
        updated_by_id INTEGER REFERENCES users(id),
        is_deleted BOOLEAN NOT NULL DEFAULT 0,
        deleted_at DATETIME
    )
''')
print('  Created raw_materials table')

print('3. Updating bom_items to use raw_material_id...')
# Check if bom_items already has raw_material_id
try:
    cur.execute("SELECT raw_material_id FROM bom_items LIMIT 1")
    print('  raw_material_id column already exists')
except sqlite3.OperationalError:
    # Create new bom_items_v2 table with raw_material_id
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bom_items_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            raw_material_id INTEGER NOT NULL REFERENCES raw_materials(id),
            quantity NUMERIC(12,2) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER REFERENCES users(id),
            updated_by_id INTEGER REFERENCES users(id)
        )
    ''')
    # Copy existing data (component_id becomes raw_material_id for now)
    try:
        cur.execute("SELECT component_id FROM bom_items LIMIT 1")
        # Migrate data if bom_items has component_id
        cur.execute('''
            INSERT OR IGNORE INTO bom_items_v2 (id, product_id, raw_material_id, quantity, created_at, updated_at, created_by_id, updated_by_id)
            SELECT id, product_id, component_id, quantity, created_at, updated_at, created_by_id, updated_by_id FROM bom_items
        ''')
        print(f'  Migrated {cur.rowcount} rows from bom_items to bom_items_v2')
    except sqlite3.OperationalError:
        pass
    
    cur.execute('DROP TABLE IF EXISTS bom_items_old')
    cur.execute('ALTER TABLE bom_items RENAME TO bom_items_old')
    cur.execute('ALTER TABLE bom_items_v2 RENAME TO bom_items')
    print('  Replaced bom_items with new schema')

print('4. Dropping product_type and is_produced from products...')
# SQLite can't drop columns directly, need to recreate
try:
    # Check if columns exist
    cur.execute("SELECT product_type FROM products LIMIT 1")
    has_product_type = True
except sqlite3.OperationalError:
    has_product_type = False

try:
    cur.execute("SELECT is_produced FROM products LIMIT 1")
    has_is_produced = True
except sqlite3.OperationalError:
    has_is_produced = False

if has_product_type or has_is_produced:
    print('  Recreating products table without product_type/is_produced...')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            unit_price NUMERIC(12,2) DEFAULT 0,
            cost_price NUMERIC(12,2) DEFAULT 0,
            category_id INTEGER NOT NULL REFERENCES product_categories(id),
            unit_id INTEGER NOT NULL REFERENCES units(id),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            min_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0,
            max_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0,
            costing_method VARCHAR(30) NOT NULL DEFAULT 'standard',
            bom_labor_cost NUMERIC(12,2) DEFAULT 0,
            bom_utility_cost NUMERIC(12,2) DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER REFERENCES users(id),
            updated_by_id INTEGER REFERENCES users(id),
            is_deleted BOOLEAN NOT NULL DEFAULT 0,
            deleted_at DATETIME
        )
    ''')
    cur.execute('''
        INSERT OR IGNORE INTO products_v2 (
            id, sku, name, description, unit_price, cost_price, category_id, unit_id,
            is_active, min_stock_level, max_stock_level, costing_method,
            bom_labor_cost, bom_utility_cost,
            created_at, updated_at, created_by_id, updated_by_id, is_deleted, deleted_at
        )
        SELECT
            id, sku, name, description, unit_price, cost_price, category_id, unit_id,
            is_active, min_stock_level, max_stock_level, costing_method,
            COALESCE(bom_labor_cost, 0), COALESCE(bom_utility_cost, 0),
            created_at, updated_at, created_by_id, updated_by_id, is_deleted, deleted_at
        FROM products
    ''')
    print(f'  Migrated {cur.rowcount} rows to products_v2')
    cur.execute('DROP TABLE IF EXISTS products_old')
    cur.execute('ALTER TABLE products RENAME TO products_old')
    cur.execute('ALTER TABLE products_v2 RENAME TO products')
    print('  Replaced products table')
else:
    print('  product_type/is_produced already removed')

conn.commit()
conn.close()
print('Done.')
