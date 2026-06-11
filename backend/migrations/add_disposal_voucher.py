import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from app import create_app
from models.models import db


def migrate():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()

        if 'disposal_vouchers' not in tables:
            db.session.execute(text('''
                CREATE TABLE disposal_vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voucher_number VARCHAR(50) NOT NULL UNIQUE,
                    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
                    voucher_date DATE NOT NULL DEFAULT (date('now')),
                    reason VARCHAR(100) NOT NULL,
                    notes TEXT,
                    status VARCHAR(30) DEFAULT 'Draft',
                    disposed_by_id INTEGER REFERENCES users(id),
                    created_by_id INTEGER REFERENCES users(id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            db.session.execute(text('CREATE INDEX ix_disposal_vouchers_voucher_number ON disposal_vouchers(voucher_number)'))
            print('Created disposal_vouchers table')

        if 'disposal_voucher_items' not in tables:
            db.session.execute(text('''
                CREATE TABLE disposal_voucher_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disposal_id INTEGER NOT NULL REFERENCES disposal_vouchers(id),
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    quantity NUMERIC(12,2) NOT NULL,
                    batch_number VARCHAR(50),
                    reason VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            print('Created disposal_voucher_items table')

        db.session.commit()
        print('Migration complete')


if __name__ == '__main__':
    migrate()
