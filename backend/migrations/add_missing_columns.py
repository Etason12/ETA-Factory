"""
Migration: Add missing columns to match current models.
Run: python backend/migrations/add_missing_columns.py
"""
import sqlite3, os

# The server's instance folder is src/instance/ (where app.py lives)
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

print('Checking columns...')

# products table
add_column('products', 'product_type', "VARCHAR(50) NOT NULL DEFAULT 'Finished Good'")

# companies table
add_column('companies', 'is_deleted', 'BOOLEAN NOT NULL DEFAULT 0')
add_column('companies', 'deleted_at', 'DATETIME')

# sales_order_items - missing cost_price
add_column('sales_order_items', 'cost_price', 'NUMERIC(12,2) DEFAULT 0')

conn.commit()
conn.close()
print('Done.')
