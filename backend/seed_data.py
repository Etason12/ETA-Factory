import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import create_app
from models.models import db, Role, Permission, User, Branch, Warehouse, ProductCategory, Unit, Product, Customer, Company
from datetime import date
import bcrypt


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if Role.query.first():
            print('Database already seeded.')
            return

        roles_data = [
            {'name': 'Owner', 'description': 'Full system access', 'is_system': True},
            {'name': 'General Manager', 'description': 'Manage all branches', 'is_system': True},
            {'name': 'Branch Manager', 'description': 'Manage assigned branch', 'is_system': True},
            {'name': 'Sales Manager', 'description': 'Manage sales operations', 'is_system': True},
            {'name': 'Sales Officer', 'description': 'Create sales documents', 'is_system': True},
            {'name': 'Warehouse Manager', 'description': 'Manage warehouse operations', 'is_system': True},
            {'name': 'Store Keeper', 'description': 'Handle goods movement', 'is_system': True},
            {'name': 'Production Manager', 'description': 'Manage production', 'is_system': True},
            {'name': 'Accountant', 'description': 'Handle finances', 'is_system': True},
            {'name': 'Auditor', 'description': 'Read-only access', 'is_system': True},
        ]

        roles = {}
        for r in roles_data:
            role = Role(**r)
            db.session.add(role)
            roles[role.name] = role

        db.session.flush()

        permission_data = [
            ('users.view', 'View users', 'Users'),
            ('users.create', 'Create users', 'Users'),
            ('users.edit', 'Edit users', 'Users'),
            ('users.delete', 'Delete users', 'Users'),
            ('branches.view', 'View branches', 'Branches'),
            ('branches.create', 'Create branches', 'Branches'),
            ('branches.edit', 'Edit branches', 'Branches'),
            ('branches.delete', 'Delete branches', 'Branches'),
            ('products.view', 'View products', 'Products'),
            ('products.create', 'Create products', 'Products'),
            ('products.edit', 'Edit products', 'Products'),
            ('products.delete', 'Delete products', 'Products'),
            ('inventory.view', 'View inventory', 'Inventory'),
            ('inventory.adjust', 'Adjust inventory', 'Inventory'),
            ('inventory.edit', 'Edit inventory', 'Inventory'),
            ('warehouses.view', 'View warehouses', 'Warehouses'),
            ('warehouses.create', 'Create warehouses', 'Warehouses'),
            ('warehouses.edit', 'Edit warehouses', 'Warehouses'),
            ('warehouses.delete', 'Delete warehouses', 'Warehouses'),
            ('sales.view', 'View sales', 'Sales'),
            ('sales.create', 'Create sales', 'Sales'),
            ('sales.approve', 'Approve sales', 'Sales'),
            ('sales.delete', 'Delete sales', 'Sales'),
            ('production.view', 'View production', 'Production'),
            ('production.create', 'Create production', 'Production'),
            ('production.approve', 'Approve production', 'Production'),
            ('transfers.view', 'View transfers', 'Transfers'),
            ('transfers.create', 'Create transfers', 'Transfers'),
            ('transfers.approve', 'Approve transfers', 'Transfers'),
            ('reports.view', 'View reports', 'Reports'),
            ('audit.view', 'View audit logs', 'Audit'),
            ('customers.view', 'View customers', 'Customers'),
            ('customers.create', 'Create customers', 'Customers'),
            ('customers.edit', 'Edit customers', 'Customers'),
            ('customers.delete', 'Delete customers', 'Customers'),
            ('payments.create', 'Create payments', 'Payments'),
            ('payments.view', 'View payments', 'Payments'),
        ]

        permissions = {}
        for name, desc, module in permission_data:
            perm = Permission(name=name, description=desc, module=module)
            db.session.add(perm)
            permissions[name] = perm

        owner_role = roles['Owner']
        for perm in permissions.values():
            owner_role.permissions.append(perm)

        gm_role = roles['General Manager']
        for perm_name in ['users.view', 'users.create', 'users.edit',
                           'branches.view', 'branches.create', 'branches.edit', 'branches.delete',
                          'products.view', 'products.create', 'products.edit', 'products.delete',
                           'inventory.view', 'inventory.adjust', 'inventory.edit',
                            'warehouses.view', 'warehouses.create', 'warehouses.edit', 'warehouses.delete',
                           'sales.view', 'sales.create', 'sales.approve',
                          'production.view', 'production.create', 'production.approve',
                          'transfers.view', 'transfers.create', 'transfers.approve',
                          'reports.view', 'audit.view',
                          'customers.view', 'customers.create', 'customers.edit', 'customers.delete',
                          'payments.create', 'payments.view']:
            gm_role.permissions.append(permissions[perm_name])

        bm_role = roles['Branch Manager']
        for perm_name in ['branches.view', 'products.view', 'inventory.view',
                          'warehouses.view', 'sales.view', 'sales.create',
                          'production.view', 'transfers.view', 'reports.view',
                          'customers.view', 'customers.create', 'customers.edit',
                          'payments.view']:
            bm_role.permissions.append(permissions[perm_name])

        sm_role = roles['Sales Manager']
        for perm_name in ['products.view', 'inventory.view',
                          'sales.view', 'sales.create', 'sales.approve',
                          'customers.view', 'customers.create', 'customers.edit',
                          'reports.view', 'payments.create', 'payments.view']:
            sm_role.permissions.append(permissions[perm_name])

        so_role = roles['Sales Officer']
        for perm_name in ['products.view', 'inventory.view',
                          'sales.view', 'sales.create',
                          'customers.view', 'customers.create',
                          'payments.view']:
            so_role.permissions.append(permissions[perm_name])

        wm_role = roles['Warehouse Manager']
        for perm_name in ['products.view', 'inventory.view', 'inventory.adjust', 'inventory.edit',
                           'warehouses.view', 'warehouses.create', 'warehouses.edit', 'warehouses.delete',
                           'transfers.view', 'transfers.create', 'transfers.approve',
                           'reports.view']:
            wm_role.permissions.append(permissions[perm_name])

        sk_role = roles['Store Keeper']
        for perm_name in ['products.view', 'inventory.view', 'inventory.adjust',
                          'warehouses.view',
                          'transfers.view', 'transfers.create']:
            sk_role.permissions.append(permissions[perm_name])

        pm_role = roles['Production Manager']
        for perm_name in ['products.view', 'inventory.view',
                          'production.view', 'production.create', 'production.approve',
                          'reports.view']:
            pm_role.permissions.append(permissions[perm_name])

        acc_role = roles['Accountant']
        for perm_name in ['customers.view', 'sales.view',
                          'payments.create', 'payments.view',
                          'reports.view', 'inventory.view']:
            acc_role.permissions.append(permissions[perm_name])

        aud_role = roles['Auditor']
        for perm_name in ['users.view', 'branches.view', 'products.view', 'inventory.view',
                          'warehouses.view', 'sales.view', 'production.view', 'transfers.view',
                          'reports.view', 'audit.view', 'customers.view', 'payments.view']:
            aud_role.permissions.append(permissions[perm_name])

        branches_data = [
            {'name': 'Addis Ababa Branch', 'code': 'ADD', 'city': 'Addis Ababa', 'address': 'Bole Road, Addis Ababa', 'phone': '+251-11-111-1111', 'email': 'addis@etacom.technology'},
            {'name': 'Mekelle Branch', 'code': 'MEK', 'city': 'Mekelle', 'address': 'Mekelle City Center', 'phone': '+251-34-111-1111', 'email': 'mekelle@etacom.technology'},
        ]

        branches = {}
        for b in branches_data:
            branch = Branch(**b)
            db.session.add(branch)
            branches[branch.code] = branch

        db.session.flush()

        warehouses_data = [
            {'name': 'Factory Warehouse', 'code': 'FWH', 'type': 'Factory', 'branch_id': branches['ADD'].id},
            {'name': 'Central Warehouse - Addis', 'code': 'CWH-ADD', 'type': 'Branch Warehouse', 'branch_id': branches['ADD'].id},
            {'name': 'Sales Store - Addis', 'code': 'STR-ADD', 'type': 'Sales Store', 'branch_id': branches['ADD'].id},
            {'name': 'Central Warehouse - Mekelle', 'code': 'CWH-MEK', 'type': 'Branch Warehouse', 'branch_id': branches['MEK'].id},
            {'name': 'Sales Store - Mekelle', 'code': 'STR-MEK', 'type': 'Sales Store', 'branch_id': branches['MEK'].id},
        ]

        for w in warehouses_data:
            db.session.add(Warehouse(**w))

        users_data = [
            {'username': 'owner', 'email': 'owner@etacom.technology', 'password': 'owner123', 'full_name': 'System Owner', 'role': 'Owner'},
            {'username': 'gm', 'email': 'gm@etacom.technology', 'password': 'gm123', 'full_name': 'General Manager', 'role': 'General Manager'},
            {'username': 'bm_addis', 'email': 'bm.addis@etacom.technology', 'password': 'bm123', 'full_name': 'Addis Branch Manager', 'role': 'Branch Manager', 'branch_code': 'ADD'},
            {'username': 'bm_mekelle', 'email': 'bm.mekelle@etacom.technology', 'password': 'bm123', 'full_name': 'Mekelle Branch Manager', 'role': 'Branch Manager', 'branch_code': 'MEK'},
            {'username': 'sm', 'email': 'sm@etacom.technology', 'password': 'sm123', 'full_name': 'Sales Manager', 'role': 'Sales Manager'},
            {'username': 'so', 'email': 'so@etacom.technology', 'password': 'so123', 'full_name': 'Sales Officer', 'role': 'Sales Officer', 'branch_code': 'ADD'},
            {'username': 'wm', 'email': 'wm@etacom.technology', 'password': 'wm123', 'full_name': 'Warehouse Manager', 'role': 'Warehouse Manager'},
            {'username': 'sk', 'email': 'sk@etacom.technology', 'password': 'sk123', 'full_name': 'Store Keeper', 'role': 'Store Keeper', 'branch_code': 'ADD'},
            {'username': 'pm', 'email': 'pm@etacom.technology', 'password': 'pm123', 'full_name': 'Production Manager', 'role': 'Production Manager'},
            {'username': 'accountant', 'email': 'accountant@etacom.technology', 'password': 'acc123', 'full_name': 'Accountant', 'role': 'Accountant'},
            {'username': 'auditor', 'email': 'auditor@etacom.technology', 'password': 'aud123', 'full_name': 'Auditor', 'role': 'Auditor'},
        ]

        for u in users_data:
            password_hash = bcrypt.hashpw(u['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(
                username=u['username'],
                email=u['email'],
                password_hash=password_hash,
                full_name=u['full_name'],
                role_id=roles[u['role']].id,
                branch_id=branches.get(u.get('branch_code', '')).id if u.get('branch_code') else None,
                is_active=True
            )
            db.session.add(user)

        categories_data = [
            {'name': 'Finished Fabric', 'description': 'Finished fabric products'},
            {'name': 'Yarn', 'description': 'Yarn and thread products'},
            {'name': 'Raw Cotton', 'description': 'Raw cotton materials'},
            {'name': 'Packaging', 'description': 'Packaging materials'},
        ]

        for c in categories_data:
            db.session.add(ProductCategory(**c))

        units_data = [
            {'name': 'Meter', 'abbreviation': 'm'},
            {'name': 'Kilogram', 'abbreviation': 'kg'},
            {'name': 'Piece', 'abbreviation': 'pcs'},
            {'name': 'Roll', 'abbreviation': 'rl'},
            {'name': 'Liter', 'abbreviation': 'L'},
        ]

        for u in units_data:
            db.session.add(Unit(**u))

        db.session.flush()

        products_data = [
            {'sku': 'TF-001', 'name': 'Premium Cotton Fabric White', 'category_id': 1, 'unit_id': 1, 'unit_price': 150.00, 'cost_price': 100.00},
            {'sku': 'TF-002', 'name': 'Premium Cotton Fabric Blue', 'category_id': 1, 'unit_id': 1, 'unit_price': 160.00, 'cost_price': 110.00},
            {'sku': 'TF-003', 'name': 'Polyester Fabric Red', 'category_id': 1, 'unit_id': 1, 'unit_price': 120.00, 'cost_price': 80.00},
            {'sku': 'TF-004', 'name': 'Cotton Yarn 20s', 'category_id': 2, 'unit_id': 2, 'unit_price': 200.00, 'cost_price': 150.00},
            {'sku': 'TF-005', 'name': 'Cotton Yarn 30s', 'category_id': 2, 'unit_id': 2, 'unit_price': 250.00, 'cost_price': 180.00},
            {'sku': 'TF-006', 'name': 'Raw Cotton Grade A', 'category_id': 3, 'unit_id': 2, 'unit_price': 80.00, 'cost_price': 50.00},
        ]

        for p in products_data:
            db.session.add(Product(**p))

        db.session.flush()

        company = Company(
            name='Eta Factory ERP',
            legal_name='EtaCom Technology PLC',
            tax_id='TIN-ETA-001',
            address='Bole Road, Addis Ababa, Ethiopia',
            phone='+251-11-554-4333',
            email='info@etacom.technology',
            website='https://etacom.technology',
            currency='ETB',
            fiscal_year_start='07-01',
            is_active=True,
        )
        db.session.add(company)

        customers_data = [
            {'customer_code': 'CUST-001', 'name': 'Addis Textile PLC', 'phone': '+251-11-222-3333', 'email': 'info@addistextile.com', 'address': 'Bole, Addis Ababa', 'tin_number': 'TIN-10001', 'branch_id': branches['ADD'].id},
            {'customer_code': 'CUST-002', 'name': 'Mekelle Garments', 'phone': '+251-34-222-4444', 'email': 'info@mekellegarments.com', 'address': 'Mekelle', 'tin_number': 'TIN-10002', 'branch_id': branches['MEK'].id},
            {'customer_code': 'CUST-003', 'name': 'Ethio Fashion House', 'phone': '+251-11-333-5555', 'email': 'info@ethiofashion.com', 'address': 'Kazanchis, Addis Ababa', 'tin_number': 'TIN-10003', 'branch_id': branches['ADD'].id},
        ]

        for c in customers_data:
            db.session.add(Customer(**c))

        db.session.commit()
        print('Database seeded successfully!')
        print('Login Credentials:')
        print('  owner / owner123')
        print('  gm / gm123')
        print('  bm_addis / bm123')
        print('  bm_mekelle / bm123')
        print('  sm / sm123')
        print('  so / so123')
        print('  wm / wm123')
        print('  sk / sk123')
        print('  pm / pm123')
        print('  accountant / acc123')
        print('  auditor / aud123')


if __name__ == '__main__':
    seed()
