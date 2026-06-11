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
        cols = [c['name'] for c in inspector.get_columns('products')]

        if 'min_stock_level' not in cols:
            db.session.execute(text('ALTER TABLE products ADD COLUMN min_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0'))
            print('Added min_stock_level to products')

        if 'max_stock_level' not in cols:
            db.session.execute(text('ALTER TABLE products ADD COLUMN max_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0'))
            print('Added max_stock_level to products')

        db.session.execute(text("""
            UPDATE products
            SET min_stock_level = (
                SELECT COALESCE(MAX(inv.min_stock_level), 0)
                FROM inventory inv
                WHERE inv.product_id = products.id
            ),
            max_stock_level = (
                SELECT COALESCE(MAX(inv.max_stock_level), 0)
                FROM inventory inv
                WHERE inv.product_id = products.id
            )
        """))
        print('Copied existing thresholds from inventory to products')

        db.session.commit()
        print('Migration complete')


if __name__ == '__main__':
    migrate()
