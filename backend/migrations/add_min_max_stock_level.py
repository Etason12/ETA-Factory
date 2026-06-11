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
        columns = [c['name'] for c in inspector.get_columns('inventory')]

        if 'min_stock_level' not in columns:
            db.session.execute(text('ALTER TABLE inventory ADD COLUMN min_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0'))
            print('Added min_stock_level column')

        if 'max_stock_level' not in columns:
            db.session.execute(text('ALTER TABLE inventory ADD COLUMN max_stock_level NUMERIC(12,2) NOT NULL DEFAULT 0'))
            print('Added max_stock_level column')

        db.session.commit()
        print('Migration complete')


if __name__ == '__main__':
    migrate()
