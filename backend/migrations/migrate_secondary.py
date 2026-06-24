import sqlite3, os
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'eta_dev.db')
print('Target DB:', db_path)
if not os.path.exists(db_path):
    print('Not found')
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    def add_column(table, column, col_type):
        try:
            cur.execute('ALTER TABLE "{}" ADD COLUMN "{}" {}'.format(table, column, col_type))
            print('  Added {}.{}'.format(table, column))
        except sqlite3.OperationalError as e:
            if 'duplicate' not in str(e).lower():
                raise
    add_column('products', 'bom_labor_cost', 'NUMERIC(12,2) DEFAULT 0')
    add_column('products', 'bom_utility_cost', 'NUMERIC(12,2) DEFAULT 0')
    cur.execute('''CREATE TABLE IF NOT EXISTS raw_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, sku VARCHAR(50) NOT NULL UNIQUE, name VARCHAR(200) NOT NULL, description TEXT, cost_price NUMERIC(12,2) DEFAULT 0, unit_id INTEGER NOT NULL REFERENCES units(id), is_active BOOLEAN NOT NULL DEFAULT 1, min_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0, max_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0, stock_quantity NUMERIC(12,2) NOT NULL DEFAULT 0, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, created_by_id INTEGER REFERENCES users(id), updated_by_id INTEGER REFERENCES users(id), is_deleted BOOLEAN NOT NULL DEFAULT 0, deleted_at DATETIME)''')
    # bom_items: add raw_material_id column
    try:
        cur.execute("SELECT raw_material_id FROM bom_items LIMIT 1")
    except sqlite3.OperationalError:
        # Create new bom_items, copy data, swap
        cur.execute('''CREATE TABLE IF NOT EXISTS bom_items_v2 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL REFERENCES products(id), raw_material_id INTEGER NOT NULL REFERENCES raw_materials(id), quantity NUMERIC(12,2) NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, created_by_id INTEGER REFERENCES users(id), updated_by_id INTEGER REFERENCES users(id))''')
        try:
            cur.execute("SELECT component_id FROM bom_items LIMIT 1")
            cur.execute('''INSERT OR IGNORE INTO bom_items_v2 (id, product_id, raw_material_id, quantity, created_at, updated_at, created_by_id, updated_by_id) SELECT id, product_id, component_id, quantity, created_at, updated_at, created_by_id, updated_by_id FROM bom_items''')
        except sqlite3.OperationalError:
            pass
        cur.execute('DROP TABLE IF EXISTS bom_items_old')
        cur.execute('ALTER TABLE bom_items RENAME TO bom_items_old')
        cur.execute('ALTER TABLE bom_items_v2 RENAME TO bom_items')
    conn.commit()
    conn.close()
    print('Done')
