import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from app import create_app
from models.models import db, Role, Permission

def migrate():
    app = create_app()
    with app.app_context():
        for perm_name, role_names in [
            ('warehouses.delete', ['General Manager', 'Warehouse Manager']),
            ('branches.delete', ['General Manager']),
        ]:
            perm = Permission.query.filter_by(name=perm_name).first()
            if not perm:
                print(f'Permission {perm_name} not found')
                continue

            for role in Role.query.filter(Role.name.in_(role_names)).all():
                if perm not in role.permissions:
                    role.permissions.append(perm)
                    print(f'Added {perm_name} to {role.name}')
                else:
                    print(f'{role.name} already has {perm_name}')

        db.session.commit()
        print('Migration complete')

if __name__ == '__main__':
    migrate()
