"""Seed demo data for Selam Terranite & Terrazzo."""
import sys, os
_src = os.path.join(os.path.dirname(__file__), 'src')
if _src not in sys.path:
    sys.path.insert(0, _src)

from app import create_app
from models.models import db, Company, Role, Permission, RolePermission, User, Branch, Warehouse
from models.models import ProductCategory, Unit, Product, Customer, Inventory, InventoryLedger
from models.models import SalesQuotation, SalesQuotationItem, SalesOrder, SalesOrderItem
from models.models import Invoice, Payment, GoodsReceiveVoucher, GRVItem, GoodsIssueVoucher
from models.models import GIVItem, Transfer, TransferItem, ProductionBatch
from datetime import date, datetime, timedelta, timezone
import random
import bcrypt

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── Company ──
    company = Company(
        name='Selam Terranite & Terrazzo',
        legal_name='Selam Terranite & Terrazzo PLC',
        tax_id='ST-2006-0042',
        address='Romant Square, Mekelle, Tigray, Ethiopia',
        phone='+251-941-718-888',
        email='terranitesales@gmail.com',
        website='https://www.selamterranite.com',
        currency='ETB',
        fiscal_year_start='07-01',
    )
    db.session.add(company)

    # ── Roles ──
    role_data = [
        ('Owner', 'Full system access', True),
        ('General Manager', 'Operational oversight', True),
        ('Warehouse Manager', 'Warehouse operations', True),
        ('Sales Rep', 'Sales & quotations', True),
        ('Auditor', 'Read-only audit access', True),
        ('Accountant', 'Financial transactions', True),
        ('Production Manager', 'Factory production oversight', True),
    ]
    roles = {}
    for name, desc, sys_flag in role_data:
        r = Role(name=name, description=desc, is_system=sys_flag)
        db.session.add(r)
        roles[name] = r
    db.session.flush()

    # ── Permissions ──
    modules = ['dashboard', 'users', 'branches', 'warehouses', 'products', 'customers',
               'inventory', 'sales', 'invoices', 'payments', 'transfers', 'production',
               'reports', 'audit', 'settings']
    actions = ['view', 'create', 'edit', 'delete']
    perm_map = {}
    for m in modules:
        for a in actions:
            pname = f'{m}.{a}'
            p = Permission(name=pname, description=f'{a} {m}', module=m)
            db.session.add(p)
            perm_map[pname] = p
    db.session.flush()

    def grant(role_name, *perms):
        r = roles[role_name]
        for pname in perms:
            if pname in perm_map:
                rp = RolePermission.query.filter_by(role_id=r.id, permission_id=perm_map[pname].id).first()
                if not rp:
                    db.session.add(RolePermission(role_id=r.id, permission_id=perm_map[pname].id))

    for p in perm_map.values():
        grant('Owner', p.name)

    gm_modules = ['dashboard', 'users', 'branches', 'warehouses', 'products', 'customers',
                  'inventory', 'sales', 'invoices', 'payments', 'transfers', 'production', 'reports']
    for m in gm_modules:
        for a in ('view', 'create', 'edit'):
            grant('General Manager', f'{m}.{a}')
        grant('General Manager', f'{m}.delete')

    for m in ('warehouses', 'products', 'inventory', 'transfers', 'dashboard'):
        for a in ('view', 'create', 'edit'):
            grant('Warehouse Manager', f'{m}.{a}')

    for m in ('customers', 'sales', 'dashboard', 'products'):
        for a in ('view', 'create', 'edit'):
            grant('Sales Rep', f'{m}.{a}')

    for m in modules:
        if m != 'settings':
            grant('Auditor', f'{m}.view')

    for m in ('invoices', 'payments', 'customers', 'dashboard'):
        for a in ('view', 'create', 'edit'):
            grant('Accountant', f'{m}.{a}')

    for m in ('production', 'products', 'inventory', 'dashboard', 'warehouses'):
        for a in ('view', 'create', 'edit'):
            grant('Production Manager', f'{m}.{a}')

    # ── Branches ──
    branch_data = [
        ('Mekelle HQ', 'MKE-001', 'Mekelle', 'Romant Square, In front of LG Building', '+251-941-718-888', 'mekelle@selamterranite.com'),
        ('Addis Ababa Sales Office', 'ADD-001', 'Addis Ababa', 'Bole Sub-city, Woreda 03', '+251-941-712-222', 'addis@selamterranite.com'),
        ('Mekelle Factory 1', 'MKF-01', 'Mekelle', 'Industrial Zone, Plot 7A', '+251-941-714-444', 'factory1@selamterranite.com'),
        ('Mekelle Factory 2', 'MKF-02', 'Mekelle', 'Industrial Zone, Plot 12B', '+251-941-714-444', 'factory2@selamterranite.com'),
        ('Addis Factory 3', 'ADF-03', 'Addis Ababa', 'Legetafo Industrial Park', '+251-941-713-333', 'factory3@selamterranite.com'),
    ]
    branches = {}
    for name, code, city, addr, phone, email in branch_data:
        b = Branch(name=name, code=code, city=city, address=addr, phone=phone, email=email, is_active=True)
        db.session.add(b)
        branches[name] = b
    db.session.flush()

    # ── Warehouses ──
    wh_data = [
        ('Finished Goods - HQ', 'WH-MKE-FG', 'Finished Goods', branches['Mekelle HQ'].id),
        ('Raw Materials - HQ', 'WH-MKE-RM', 'Raw Materials', branches['Mekelle HQ'].id),
        ('Finished Goods - Addis', 'WH-ADD-FG', 'Finished Goods', branches['Addis Ababa Sales Office'].id),
        ('Factory 1 Warehouse', 'WH-F1-WH', 'Finished Goods', branches['Mekelle Factory 1'].id),
        ('Factory 1 Raw Materials', 'WH-F1-RM', 'Raw Materials', branches['Mekelle Factory 1'].id),
        ('Factory 2 Warehouse', 'WH-F2-WH', 'Finished Goods', branches['Mekelle Factory 2'].id),
        ('Factory 3 Warehouse', 'WH-F3-WH', 'Finished Goods', branches['Addis Factory 3'].id),
    ]
    warehouses = {}
    for name, code, wtype, bid in wh_data:
        w = Warehouse(name=name, code=code, type=wtype, branch_id=bid, is_active=True)
        db.session.add(w)
        warehouses[name] = w
    db.session.flush()

    # ── Users ──
    user_data = [
        (1, 'owner', 'owner@selamterranite.com', 'Solomon Tadesse', '0911-700-001', roles['Owner'].id, branches['Mekelle HQ'].id),
        (2, 'gm', 'gm@selamterranite.com', 'Meron Alemu', '0911-700-002', roles['General Manager'].id, branches['Mekelle HQ'].id),
        (3, 'whmgraddis', 'wh@addis.selamterranite.com', 'Dawit Hailu', '0911-700-003', roles['Warehouse Manager'].id, branches['Mekelle Factory 1'].id),
        (4, 'whmgrbahir', 'wh@bahirdar.selamterranite.com', 'Yeshiwork Assefa', '0911-700-004', roles['Warehouse Manager'].id, branches['Addis Factory 3'].id),
        (5, 'sales1', 'sales@selamterranite.com', 'Biruk Tesfaye', '0911-700-005', roles['Sales Rep'].id, branches['Addis Ababa Sales Office'].id),
        (6, 'auditor1', 'audit@selamterranite.com', 'Ephrem Girma', '0911-700-006', roles['Auditor'].id, None),
        (7, 'accountant1', 'acc@selamterranite.com', 'Hiwot Desta', '0911-700-007', roles['Accountant'].id, branches['Mekelle HQ'].id),
        (8, 'prodmgraddis', 'prod@selamterranite.com', 'Gemechu Abebe', '0911-700-008', roles['Production Manager'].id, branches['Mekelle Factory 1'].id),
    ]
    users = {}
    for uid, uname, email, full, phone, rid, bid in user_data:
        u = User(id=uid, username=uname, email=email, full_name=full, phone=phone,
                 password_hash=bcrypt.hashpw(f'{uname}123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                 role_id=rid, branch_id=bid, is_active=True)
        db.session.add(u)
        users[uname] = u
    db.session.flush()

    # ── Product Categories ──
    cat_data = ['Terranite Tiles', 'Terrazzo Tiles', 'Terrazzo Stairs', 'Raw Materials', 'Chemicals & Additives']
    cats = {}
    for name in cat_data:
        obj = ProductCategory(name=name)
        db.session.add(obj)
        cats[name] = obj
    db.session.flush()

    # ── Units ──
    unit_data = [('Square Meters', 'm2'), ('Pieces', 'pcs'), ('Boxes', 'bx'), ('Kilograms', 'kg'), ('Liters', 'L'), ('Bags', 'bag'), ('Tons', 'ton')]
    units = {}
    for name, abbr in unit_data:
        obj = Unit(name=name, abbreviation=abbr)
        db.session.add(obj)
        units[name] = obj
    db.session.flush()

    # ── Products ──
    product_data = [
        # Terranite Tiles
        ('TRN-33N', 'Terranite Tile 33x33 Natural', 'Natural grey terranite tile 33x33cm', 185.00, 110.00, cats['Terranite Tiles'], units['Pieces']),
        ('TRN-33R', 'Terranite Tile 33x33 Red', 'Red terranite tile 33x33cm', 195.00, 115.00, cats['Terranite Tiles'], units['Pieces']),
        ('TRN-40N', 'Terranite Tile 40x40 Natural', 'Natural grey terranite tile 40x40cm', 245.00, 145.00, cats['Terranite Tiles'], units['Pieces']),
        ('TRN-40R', 'Terranite Tile 40x40 Red', 'Red terranite tile 40x40cm', 255.00, 150.00, cats['Terranite Tiles'], units['Pieces']),
        ('TRN-50N', 'Terranite Tile 50x50 Natural', 'Natural grey terranite tile 50x50cm', 380.00, 240.00, cats['Terranite Tiles'], units['Pieces']),
        ('TRN-50W', 'Terranite Tile 50x50 White', 'White terranite tile 50x50cm', 420.00, 260.00, cats['Terranite Tiles'], units['Pieces']),
        ('TRN-60N', 'Terranite Tile 60x60 Natural', 'Natural grey terranite tile 60x60cm', 520.00, 330.00, cats['Terranite Tiles'], units['Pieces']),
        # Terrazzo Tiles
        ('TRZ-25G', 'Terrazzo Tile 25x25 Green', 'Green terrazzo tile 25x25cm', 95.00, 55.00, cats['Terrazzo Tiles'], units['Pieces']),
        ('TRZ-25W', 'Terrazzo Tile 25x25 White', 'White terrazzo tile 25x25cm', 90.00, 52.00, cats['Terrazzo Tiles'], units['Pieces']),
        ('TRZ-30G', 'Terrazzo Tile 30x30 Green', 'Green terrazzo tile 30x30cm', 125.00, 72.00, cats['Terrazzo Tiles'], units['Pieces']),
        ('TRZ-30W', 'Terrazzo Tile 30x30 White', 'White terrazzo tile 30x30cm', 120.00, 68.00, cats['Terrazzo Tiles'], units['Pieces']),
        ('TRZ-40G', 'Terrazzo Tile 40x40 Green', 'Green terrazzo tile 40x40cm', 175.00, 100.00, cats['Terrazzo Tiles'], units['Pieces']),
        ('TRZ-40W', 'Terrazzo Tile 40x40 White', 'White terrazzo tile 40x40cm', 165.00, 95.00, cats['Terrazzo Tiles'], units['Pieces']),
        # Terrazzo Stairs
        ('STS-100', 'Terrazzo Stair Tread Standard', 'Standard terrazzo stair tread 100x35cm', 350.00, 210.00, cats['Terrazzo Stairs'], units['Pieces']),
        ('STS-120', 'Terrazzo Stair Tread Wide', 'Wide terrazzo stair tread 120x40cm', 450.00, 270.00, cats['Terrazzo Stairs'], units['Pieces']),
        ('STS-RIS', 'Terrazzo Stair Riser', 'Terrazzo stair riser 100x15cm', 180.00, 105.00, cats['Terrazzo Stairs'], units['Pieces']),
        # Raw Materials
        ('RM-CEM', 'Portland Cement Grade 42.5', 'High-grade Portland cement for tile production', 850.00, 620.00, cats['Raw Materials'], units['Bags']),
        ('RM-MAR', 'Marble Aggregate Fine', 'Fine marble aggregate 0-3mm for terrazzo', 1200.00, 800.00, cats['Raw Materials'], units['Tons']),
        ('RM-MAR-C', 'Marble Aggregate Coarse', 'Coarse marble aggregate 3-7mm for terrazzo', 1100.00, 750.00, cats['Raw Materials'], units['Tons']),
        ('RM-PIG-B', 'Iron Oxide Pigment - Black', 'Black iron oxide pigment for tile coloring 25kg', 3500.00, 2200.00, cats['Chemicals & Additives'], units['Bags']),
        ('RM-PIG-R', 'Iron Oxide Pigment - Red', 'Red iron oxide pigment for tile coloring 25kg', 3800.00, 2400.00, cats['Chemicals & Additives'], units['Bags']),
        ('RM-PIG-W', 'Titanium Dioxide - White', 'White titanium dioxide pigment 25kg', 5200.00, 3800.00, cats['Chemicals & Additives'], units['Bags']),
    ]
    products = {}
    for sku, name, desc, up, cp, cat, unit in product_data:
        p = Product(sku=sku, name=name, description=desc, unit_price=up, cost_price=cp,
                    category_id=cat.id, unit_id=unit.id, is_active=True)
        db.session.add(p)
        products[name] = p
    db.session.flush()

    # ── Customers ──
    customer_data = [
        ('ST-C-001', 'Mekelle University', '0911-800-001', 'procurement@mu.edu.et', 'Mekelle University Main Campus', 'ET-MU-001', 'Institutional', 2500000),
        ('ST-C-002', 'Woldia University', '0911-800-002', 'procurement@wldu.edu.et', 'Woldia, Amhara Region', 'ET-WU-002', 'Institutional', 1800000),
        ('ST-C-003', 'Debre Birhan University', '0911-800-003', 'procurement@dbu.edu.et', 'Debre Birhan, Amhara Region', 'ET-DB-003', 'Institutional', 2000000),
        ('ST-C-004', 'Sunshine Construction PLC', '0911-800-004', 'info@sunshineconstruction.et', 'Bole Road, Addis Ababa', 'ET-SC-004', 'Wholesale', 5000000),
        ('ST-C-005', 'Tigray Building Materials', '0911-800-005', 'orders@tigraybuild.et', 'Mekelle, Romant Square', 'ET-TB-005', 'Retail', 750000),
        ('ST-C-006', 'Arada Real Estate SC', '0911-800-006', 'procurement@aradarealestate.et', 'CMC Area, Addis Ababa', 'ET-AR-006', 'Wholesale', 4000000),
        ('ST-C-007', 'Axum Hotel PLC', '0911-800-007', 'info@axumhotel.et', 'Piazza, Axum, Tigray', 'ET-AH-007', 'Retail', 900000),
        ('ST-C-008', 'Ethio-Cement Distributors', '0911-800-008', 'sales@ethiocement.et', 'Industrial Zone, Dire Dawa', 'ET-EC-008', 'Distributor', 3000000),
    ]
    customers = {}
    for code, name, phone, email, addr, tin, ctype, cl in customer_data:
        cust = Customer(customer_code=code, name=name, phone=phone, email=email, address=addr,
                        tin_number=tin, customer_type=ctype, credit_limit=cl, is_active=True,
                        branch_id=branches['Mekelle HQ'].id)
        db.session.add(cust)
        customers[name] = cust
    db.session.flush()

    # ── Inventory ──
    fg_wh = warehouses['Factory 1 Warehouse']
    addis_wh = warehouses['Finished Goods - Addis']
    rm_wh = warehouses['Factory 1 Raw Materials']
    fg2_wh = warehouses['Factory 2 Warehouse']

    finished_stock = [
        (products['Terranite Tile 33x33 Natural'], 800),
        (products['Terranite Tile 33x33 Red'], 400),
        (products['Terranite Tile 40x40 Natural'], 600),
        (products['Terranite Tile 40x40 Red'], 300),
        (products['Terranite Tile 50x50 Natural'], 250),
        (products['Terranite Tile 50x50 White'], 150),
        (products['Terranite Tile 60x60 Natural'], 100),
        (products['Terrazzo Tile 25x25 Green'], 500),
        (products['Terrazzo Tile 25x25 White'], 500),
        (products['Terrazzo Tile 30x30 Green'], 350),
        (products['Terrazzo Tile 30x30 White'], 400),
        (products['Terrazzo Tile 40x40 Green'], 200),
        (products['Terrazzo Tile 40x40 White'], 250),
        (products['Terrazzo Stair Tread Standard'], 120),
        (products['Terrazzo Stair Tread Wide'], 80),
        (products['Terrazzo Stair Riser'], 150),
    ]

    raw_stock = [
        (products['Portland Cement Grade 42.5'], 200),
        (products['Marble Aggregate Fine'], 50),
        (products['Marble Aggregate Coarse'], 40),
        (products['Iron Oxide Pigment - Black'], 30),
        (products['Iron Oxide Pigment - Red'], 25),
        (products['Titanium Dioxide - White'], 20),
    ]

    for prod, qty in finished_stock:
        inv = Inventory(product_id=prod.id, warehouse_id=fg_wh.id, quantity_on_hand=qty, reserved_quantity=0)
        db.session.add(inv)
        db.session.add(InventoryLedger(product_id=prod.id, warehouse_id=fg_wh.id,
            movement_type='Opening Balance', quantity=qty,
            unit_cost=prod.cost_price, reference_type='Seed',
            transaction_date=datetime.now(timezone.utc) - timedelta(days=45)))

        inv_a = Inventory(product_id=prod.id, warehouse_id=addis_wh.id,
                          quantity_on_hand=max(qty // 3, 20), reserved_quantity=0)
        db.session.add(inv_a)
        db.session.add(InventoryLedger(product_id=prod.id, warehouse_id=addis_wh.id,
            movement_type='Opening Balance', quantity=inv_a.quantity_on_hand,
            unit_cost=prod.cost_price, reference_type='Seed',
            transaction_date=datetime.now(timezone.utc) - timedelta(days=30)))

    for prod, qty in raw_stock:
        inv = Inventory(product_id=prod.id, warehouse_id=rm_wh.id, quantity_on_hand=qty, reserved_quantity=0)
        db.session.add(inv)
        db.session.add(InventoryLedger(product_id=prod.id, warehouse_id=rm_wh.id,
            movement_type='Opening Balance', quantity=qty,
            unit_cost=prod.cost_price, reference_type='Seed',
            transaction_date=datetime.now(timezone.utc) - timedelta(days=30)))

    # Extra stock in Factory 2
    for prod, qty in finished_stock[:8]:
        inv = Inventory(product_id=prod.id, warehouse_id=fg2_wh.id,
                        quantity_on_hand=qty // 2, reserved_quantity=0)
        db.session.add(inv)
    db.session.flush()

    # ── Sales Quotations ──
    qt_now = datetime.now(timezone.utc)
    q1 = SalesQuotation(
        quotation_number='ST-QT-2024-001',
        customer_id=customers['Mekelle University'].id,
        branch_id=branches['Mekelle HQ'].id, status='Approved',
        valid_until=date.today() + timedelta(days=45),
        subtotal=0, tax_amount=0, total_amount=0,
        notes='Phase 1 - Science block flooring',
        created_by_id=users['sales1'].id)
    db.session.add(q1)
    db.session.flush()
    q1_items = [
        (q1.id, products['Terranite Tile 40x40 Natural'].id, 500, 245.00),
        (q1.id, products['Terrazzo Tile 30x30 White'].id, 300, 120.00),
        (q1.id, products['Terrazzo Stair Tread Standard'].id, 50, 350.00),
        (q1.id, products['Terrazzo Stair Riser'].id, 50, 180.00),
    ]
    subt = 0
    for qi, pid, qty, up in q1_items:
        total = qty * up
        subt += total
        db.session.add(SalesQuotationItem(quotation_id=qi, product_id=pid, quantity=qty, unit_price=up, total_price=total))
    q1.subtotal = subt
    q1.tax_amount = round(subt * 0.15, 2)
    q1.total_amount = subt + q1.tax_amount

    q2 = SalesQuotation(
        quotation_number='ST-QT-2024-002',
        customer_id=customers['Arada Real Estate SC'].id,
        branch_id=branches['Addis Ababa Sales Office'].id, status='Draft',
        valid_until=date.today() + timedelta(days=30),
        subtotal=0, tax_amount=0, total_amount=0,
        notes='New residential complex - 4 buildings',
        created_by_id=users['sales1'].id)
    db.session.add(q2)
    db.session.flush()
    q2_items = [
        (q2.id, products['Terranite Tile 60x60 Natural'].id, 200, 520.00),
        (q2.id, products['Terranite Tile 33x33 Red'].id, 400, 195.00),
        (q2.id, products['Terrazzo Tile 40x40 White'].id, 350, 165.00),
    ]
    subt2 = 0
    for qi, pid, qty, up in q2_items:
        total = qty * up
        subt2 += total
        db.session.add(SalesQuotationItem(quotation_id=qi, product_id=pid, quantity=qty, unit_price=up, total_price=total))
    q2.subtotal = subt2
    q2.tax_amount = round(subt2 * 0.15, 2)
    q2.total_amount = subt2 + q2.tax_amount

    # ── Sales Orders ──
    so1 = SalesOrder(
        order_number='ST-SO-2024-001',
        customer_id=customers['Mekelle University'].id,
        branch_id=branches['Mekelle HQ'].id,
        warehouse_id=fg_wh.id,
        quotation_id=q1.id,
        order_date=date.today() - timedelta(days=5),
        status='Confirmed',
        subtotal=0, tax_amount=0, total_amount=0,
        created_by_id=users['sales1'].id)
    db.session.add(so1)
    db.session.flush()
    so_items = [
        (so1.id, products['Terranite Tile 40x40 Natural'].id, 300, 245.00, 150),
        (so1.id, products['Terrazzo Tile 30x30 White'].id, 200, 120.00, 80),
        (so1.id, products['Terrazzo Stair Tread Standard'].id, 30, 350.00, 0),
    ]
    subt_so = 0
    for si, pid, qty, up, dq in so_items:
        total = qty * up
        subt_so += total
        db.session.add(SalesOrderItem(sales_order_id=si, product_id=pid, quantity=qty, unit_price=up, total_price=total, delivered_quantity=dq))
    so1.subtotal = subt_so
    so1.tax_amount = round(subt_so * 0.15, 2)
    so1.total_amount = subt_so + so1.tax_amount

    # ── Invoices ──
    inv1 = Invoice(
        invoice_number='ST-INV-2024-001',
        sales_order_id=so1.id,
        customer_id=customers['Mekelle University'].id,
        invoice_date=date.today() - timedelta(days=3),
        due_date=date.today() + timedelta(days=27),
        subtotal=so1.subtotal, tax_amount=so1.tax_amount, total_amount=so1.total_amount,
        paid_amount=50000.00,
        balance_due=so1.total_amount - 50000.00,
        payment_status='Partial',
        status='Active',
        notes='Partial delivery - 50% invoiced',
        created_by_id=users['accountant1'].id)
    db.session.add(inv1)

    # ── Goods Receive Voucher (raw material purchase) ──
    grv1 = GoodsReceiveVoucher(
        voucher_number='ST-GRV-2024-001',
        warehouse_id=rm_wh.id,
        voucher_date=date.today() - timedelta(days=10),
        reference_type='Purchase Order',
        status='Completed',
        notes='Monthly raw material restock',
        received_by_id=users['whmgraddis'].id)
    db.session.add(grv1)
    db.session.flush()
    for pname, qty in [('Portland Cement Grade 42.5', 100), ('Marble Aggregate Fine', 20), ('Iron Oxide Pigment - Red', 10)]:
        prod = products[pname]
        db.session.add(GRVItem(grv_id=grv1.id, product_id=prod.id, quantity=qty, unit_cost=prod.cost_price))

    # ── Goods Issue Voucher (dispatch to customer) ──
    giv1 = GoodsIssueVoucher(
        voucher_number='ST-GIV-2024-001',
        warehouse_id=fg_wh.id,
        sales_order_id=so1.id,
        voucher_date=date.today() - timedelta(days=2),
        reference_type='Sales Order',
        status='Completed',
        issued_by_id=users['whmgraddis'].id)
    db.session.add(giv1)
    db.session.flush()
    giv_items = [
        (giv1.id, products['Terranite Tile 40x40 Natural'].id, 150),
        (giv1.id, products['Terrazzo Tile 30x30 White'].id, 80),
    ]
    for gi, pid, qty in giv_items:
        db.session.add(GIVItem(giv_id=gi, product_id=pid, quantity=qty))

    # ── Transfer (Factory 1 -> Addis showroom) ──
    t1 = Transfer(
        transfer_number='ST-TRF-2024-001',
        source_warehouse_id=fg_wh.id,
        destination_warehouse_id=addis_wh.id,
        transfer_date=date.today() - timedelta(days=7),
        status='Completed',
        notes='Replenish Addis showroom stock',
        requested_by_id=users['whmgraddis'].id)
    db.session.add(t1)
    db.session.flush()
    t1_items = [
        (t1.id, products['Terranite Tile 50x50 Natural'].id, 40, 240.00),
        (t1.id, products['Terranite Tile 50x50 White'].id, 20, 260.00),
        (t1.id, products['Terrazzo Tile 40x40 White'].id, 50, 95.00),
    ]
    for ti, pid, qty, cost in t1_items:
        db.session.add(TransferItem(transfer_id=ti, product_id=pid, quantity=qty, unit_cost=cost))

    # ── Production Batch (terranite tile run) ──
    pb_product = products['Terranite Tile 33x33 Natural']
    pb1 = ProductionBatch(
        batch_number='ST-PB-2024-001',
        product_id=pb_product.id,
        quantity_produced=1200,
        production_cost=96000.00,
        production_date=date.today() - timedelta(days=14),
        warehouse_id=fg_wh.id,
        status='Approved',
        notes='Batch 7 - Standard natural terranite production run',
        created_by_id=users['prodmgraddis'].id)
    db.session.add(pb1)

    # ── Payment ──
    pmt1 = Payment(
        payment_number='ST-PMT-2024-001',
        invoice_id=inv1.id,
        customer_id=customers['Mekelle University'].id,
        amount=50000.00,
        payment_date=date.today() - timedelta(days=1),
        payment_method='Bank Transfer',
        reference_number='TRF-98765-ET',
        notes='Advance payment for Phase 1',
        received_by_id=users['accountant1'].id)
    db.session.add(pmt1)

    db.session.commit()
    print('SUCCESS: Selam Terranite demo data seeded.')
    print(f'  Company: {company.name}')
    print(f'  Users: {len(users)} (passwords: <username>123)')
    print(f'  Branches: {len(branches)}, Warehouses: {len(warehouses)}')
    print(f'  Products: {len(products)}, Categories: {len(cats)}')
    print(f'  Customers: {len(customers)}')
    print(f'  Quotations: 2, Orders: 1, Invoices: 1, Payments: 1')
    print(f'  GRV: 1, GIV: 1, Transfers: 1, Production: 1')
