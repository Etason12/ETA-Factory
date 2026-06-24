from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import get_current_user

db = SQLAlchemy()


class SoftDeleteMixin:
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='role', lazy='dynamic', foreign_keys='User.role_id')
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles', lazy='dynamic')


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    module = db.Column(db.String(50), nullable=False)


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id'),)


class User(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    last_login = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'branch_id': self.branch_id,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Branch(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    city = db.Column(db.String(100))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    warehouses = db.relationship('Warehouse', backref='branch', lazy='dynamic')
    users = db.relationship('User', backref='branch', lazy='dynamic', foreign_keys='User.branch_id')


class Warehouse(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)

    inventory = db.relationship('Inventory', backref='warehouse', lazy='dynamic')
    goods_receive_vouchers = db.relationship('GoodsReceiveVoucher', backref='warehouse', lazy='dynamic')
    goods_issue_vouchers = db.relationship('GoodsIssueVoucher', backref='warehouse', lazy='dynamic')
    disposal_vouchers = db.relationship('DisposalVoucher', backref='warehouse', lazy='dynamic')
    source_transfers = db.relationship('Transfer', backref='source_warehouse', lazy='dynamic',
                                        foreign_keys='Transfer.source_warehouse_id')
    destination_transfers = db.relationship('Transfer', backref='destination_warehouse', lazy='dynamic',
                                             foreign_keys='Transfer.destination_warehouse_id')


class ProductCategory(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)

    products = db.relationship('Product', backref='category', lazy='dynamic')


class Unit(db.Model, TimestampMixin):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    abbreviation = db.Column(db.String(10), nullable=False)

    products = db.relationship('Product', backref='unit', lazy='dynamic')


class Product(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    unit_price = db.Column(db.Numeric(12, 2), default=0)
    cost_price = db.Column(db.Numeric(12, 2), default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    min_stock_level = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    max_stock_level = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    costing_method = db.Column(db.String(30), default='standard', nullable=False)
    bom_labor_cost = db.Column(db.Numeric(12, 2), default=0)
    bom_utility_cost = db.Column(db.Numeric(12, 2), default=0)

    inventory = db.relationship('Inventory', backref='product', lazy='dynamic')
    production_batches = db.relationship('ProductionBatch', backref='product', lazy='dynamic')


class RawMaterial(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'raw_materials'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cost_price = db.Column(db.Numeric(12, 2), default=0)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    min_stock_level = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    max_stock_level = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    stock_quantity = db.Column(db.Numeric(12, 2), default=0, nullable=False)

    unit = db.relationship('Unit', backref='raw_materials', lazy='select')


class Customer(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    tin_number = db.Column(db.String(50))
    customer_type = db.Column(db.String(50), default='Regular')
    credit_limit = db.Column(db.Numeric(12, 2), default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)

    sales_quotations = db.relationship('SalesQuotation', backref='customer', lazy='dynamic')
    sales_orders = db.relationship('SalesOrder', backref='customer', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')
    payments = db.relationship('Payment', backref='customer', lazy='dynamic')


class Inventory(db.Model, TimestampMixin):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity_on_hand = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    reserved_quantity = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    batch_number = db.Column(db.String(50))
    min_stock_level = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    max_stock_level = db.Column(db.Numeric(12, 2), default=0, nullable=False)

    __table_args__ = (db.UniqueConstraint('product_id', 'warehouse_id', 'batch_number', name='uix_inventory'),)

    @property
    def available_quantity(self):
        return float(self.quantity_on_hand or 0) - float(self.reserved_quantity or 0)

    @property
    def is_low_stock(self):
        min_val = float(self.product.min_stock_level or 0) if self.product else 0
        return min_val > 0 and float(self.quantity_on_hand or 0) <= min_val


class InventoryLedger(db.Model):
    __tablename__ = 'inventory_ledger'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2))
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    batch_number = db.Column(db.String(50))
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    product = db.relationship('Product', backref='ledger_entries')
    warehouse = db.relationship('Warehouse', backref='ledger_entries')


class ProductionBatch(db.Model, TimestampMixin):
    __tablename__ = 'production_batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_produced = db.Column(db.Numeric(12, 2), nullable=False)
    production_cost = db.Column(db.Numeric(12, 2), default=0)
    production_date = db.Column(db.Date, nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='Pending')
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    warehouse = db.relationship('Warehouse', backref='production_batch_warehouse')
    creator = db.relationship('User', foreign_keys='ProductionBatch.created_by_id', lazy='joined')
    approver = db.relationship('User', foreign_keys='ProductionBatch.approved_by_id', lazy='joined')


class SalesQuotation(db.Model, TimestampMixin):
    __tablename__ = 'sales_quotations'

    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    status = db.Column(db.String(30), default='Draft')
    valid_until = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('SalesQuotationItem', backref='quotation', lazy='dynamic', cascade='all, delete-orphan')


class SalesQuotationItem(db.Model):
    __tablename__ = 'sales_quotation_items'

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('sales_quotations.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)


class SalesOrder(db.Model, TimestampMixin):
    __tablename__ = 'sales_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quotation_id = db.Column(db.Integer, db.ForeignKey('sales_quotations.id'), nullable=True)
    order_date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(30), default='Draft')
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    warehouse = db.relationship('Warehouse', backref='order_warehouse')
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy='dynamic', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='sales_order', lazy='dynamic')
    goods_issue_vouchers = db.relationship('GoodsIssueVoucher', backref='sales_order', lazy='dynamic')
    loading_authorizations = db.relationship('LoadingAuthorization', backref='sales_order', lazy='dynamic')


class SalesOrderItem(db.Model):
    __tablename__ = 'sales_order_items'

    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    delivered_quantity = db.Column(db.Numeric(12, 2), default=0)
    cost_price = db.Column(db.Numeric(12, 2), default=0)

    product = db.relationship('Product')


class Invoice(db.Model, TimestampMixin):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    invoice_date = db.Column(db.Date, default=date.today, nullable=False)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    balance_due = db.Column(db.Numeric(12, 2), default=0)
    payment_status = db.Column(db.String(30), default='Unpaid')
    status = db.Column(db.String(30), default='Active')
    notes = db.Column(db.Text)

    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')


class Payment(db.Model, TimestampMixin):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, default=date.today, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    reference_number = db.Column(db.String(100))
    bank_name = db.Column(db.String(200))
    receipt_image = db.Column(db.String(500))
    notes = db.Column(db.Text)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class GoodsReceiveVoucher(db.Model, TimestampMixin):
    __tablename__ = 'goods_receive_vouchers'

    id = db.Column(db.Integer, primary_key=True)
    voucher_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    voucher_date = db.Column(db.Date, default=date.today, nullable=False)
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='Draft')
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('GRVItem', backref='voucher', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys='GoodsReceiveVoucher.created_by_id', lazy='joined')
    receiver = db.relationship('User', foreign_keys='GoodsReceiveVoucher.received_by_id', lazy='joined')


class GRVItem(db.Model):
    __tablename__ = 'grv_items'

    id = db.Column(db.Integer, primary_key=True)
    grv_id = db.Column(db.Integer, db.ForeignKey('goods_receive_vouchers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2))
    batch_number = db.Column(db.String(50))

    product = db.relationship('Product', lazy='joined')


class GoodsIssueVoucher(db.Model, TimestampMixin):
    __tablename__ = 'goods_issue_vouchers'

    id = db.Column(db.Integer, primary_key=True)
    voucher_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=True)
    voucher_date = db.Column(db.Date, default=date.today, nullable=False)
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='Draft')
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('GIVItem', backref='voucher', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys='GoodsIssueVoucher.created_by_id', lazy='joined')
    issuer = db.relationship('User', foreign_keys='GoodsIssueVoucher.issued_by_id', lazy='joined')


class GIVItem(db.Model):
    __tablename__ = 'giv_items'

    id = db.Column(db.Integer, primary_key=True)
    giv_id = db.Column(db.Integer, db.ForeignKey('goods_issue_vouchers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    batch_number = db.Column(db.String(50))

    product = db.relationship('Product', lazy='joined')


class DisposalVoucher(db.Model, TimestampMixin):
    __tablename__ = 'disposal_vouchers'

    id = db.Column(db.Integer, primary_key=True)
    voucher_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    voucher_date = db.Column(db.Date, default=date.today, nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='Draft')
    disposed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('DisposalVoucherItem', backref='voucher', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys='DisposalVoucher.created_by_id', lazy='joined')
    disposer = db.relationship('User', foreign_keys='DisposalVoucher.disposed_by_id', lazy='joined')


class DisposalVoucherItem(db.Model):
    __tablename__ = 'disposal_voucher_items'

    id = db.Column(db.Integer, primary_key=True)
    disposal_id = db.Column(db.Integer, db.ForeignKey('disposal_vouchers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    batch_number = db.Column(db.String(50))
    reason = db.Column(db.String(100))

    product = db.relationship('Product', lazy='joined')


class Transfer(db.Model, TimestampMixin):
    __tablename__ = 'transfers'

    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    source_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    destination_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    transfer_date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(30), default='Draft')
    notes = db.Column(db.Text)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)
    giv_id = db.Column(db.Integer, db.ForeignKey('goods_issue_vouchers.id'), nullable=True)
    grv_id = db.Column(db.Integer, db.ForeignKey('goods_receive_vouchers.id'), nullable=True)

    items = db.relationship('TransferItem', backref='transfer', lazy='dynamic', cascade='all, delete-orphan')


class TransferItem(db.Model):
    __tablename__ = 'transfer_items'

    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('transfers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2))
    batch_number = db.Column(db.String(50))

    product = db.relationship('Product', backref='transfer_items')


class LoadingAuthorization(db.Model, TimestampMixin):
    __tablename__ = 'loading_authorizations'

    id = db.Column(db.Integer, primary_key=True)
    authorization_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    authorized_date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(30), default='Pending')
    authorized_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text)


class StockAdjustment(db.Model, TimestampMixin):
    __tablename__ = 'stock_adjustments'

    id = db.Column(db.Integer, primary_key=True)
    adjustment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    adjustment_date = db.Column(db.Date, default=date.today, nullable=False)
    adjustment_type = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='Draft')
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('StockAdjustmentItem', backref='adjustment', lazy='dynamic', cascade='all, delete-orphan')


class StockAdjustmentItem(db.Model):
    __tablename__ = 'stock_adjustment_items'

    id = db.Column(db.Integer, primary_key=True)
    adjustment_id = db.Column(db.Integer, db.ForeignKey('stock_adjustments.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    current_quantity = db.Column(db.Numeric(12, 2), nullable=False)
    adjusted_quantity = db.Column(db.Numeric(12, 2), nullable=False)
    difference = db.Column(db.Numeric(12, 2), nullable=False)
    batch_number = db.Column(db.String(50))


class ReturnVoucher(db.Model, TimestampMixin):
    __tablename__ = 'return_vouchers'

    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    return_date = db.Column(db.Date, default=date.today, nullable=False)
    return_type = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='Draft')
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    items = db.relationship('ReturnVoucherItem', backref='voucher', lazy='dynamic', cascade='all, delete-orphan')


class ReturnVoucherItem(db.Model):
    __tablename__ = 'return_voucher_items'

    id = db.Column(db.Integer, primary_key=True)
    return_voucher_id = db.Column(db.Integer, db.ForeignKey('return_vouchers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2))
    batch_number = db.Column(db.String(50))
    reason = db.Column(db.Text)


class BOMItem(db.Model, TimestampMixin):
    __tablename__ = 'bom_items'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)

    product = db.relationship('Product', foreign_keys=[product_id], backref=db.backref('bom_items', lazy='dynamic'))
    raw_material = db.relationship('RawMaterial', foreign_keys=[raw_material_id])

class Company(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    legal_name = db.Column(db.String(200))
    tax_id = db.Column(db.String(50))
    default_tax_rate = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    logo_url = db.Column(db.String(500))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    currency = db.Column(db.String(10), default='ETB')
    fiscal_year_start = db.Column(db.String(5), default='07-01')
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'legal_name': self.legal_name,
            'tax_id': self.tax_id,
            'logo_url': self.logo_url,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'currency': self.currency,
            'fiscal_year_start': self.fiscal_year_start,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Supplier(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    payment_terms = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')


class PurchaseOrder(db.Model, TimestampMixin):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, default=date.today, nullable=False)
    expected_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='Draft')
    notes = db.Column(db.Text)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys='PurchaseOrder.created_by_id', lazy='joined')
    approver = db.relationship('User', foreign_keys='PurchaseOrder.approved_by_id', lazy='joined')


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    quantity_ordered = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False)
    quantity_received = db.Column(db.Numeric(12, 2), default=0)

    raw_material = db.relationship('RawMaterial', lazy='joined')


class RawMaterialInventory(db.Model, TimestampMixin):
    __tablename__ = 'raw_material_inventory'

    id = db.Column(db.Integer, primary_key=True)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity_on_hand = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    reserved_quantity = db.Column(db.Numeric(12, 2), default=0, nullable=False)

    __table_args__ = (db.UniqueConstraint('raw_material_id', 'warehouse_id', name='uix_rm_inventory'),)

    raw_material = db.relationship('RawMaterial', lazy='joined')
    warehouse = db.relationship('Warehouse', lazy='joined')

    @property
    def available_quantity(self):
        return float(self.quantity_on_hand or 0) - float(self.reserved_quantity or 0)


class RawMaterialLedger(db.Model):
    __tablename__ = 'raw_material_ledger'

    id = db.Column(db.Integer, primary_key=True)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2))
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    raw_material = db.relationship('RawMaterial', lazy='joined')
    warehouse = db.relationship('Warehouse', lazy='joined')


class StoreRequisition(db.Model, TimestampMixin):
    __tablename__ = 'store_requisitions'

    id = db.Column(db.Integer, primary_key=True)
    requisition_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    production_batch_id = db.Column(db.Integer, db.ForeignKey('production_batches.id'), nullable=True)
    requisition_date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(30), default='Pending')
    notes = db.Column(db.Text)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship('StoreRequisitionItem', backref='requisition', lazy='dynamic', cascade='all, delete-orphan')
    warehouse = db.relationship('Warehouse', lazy='joined')
    production_batch = db.relationship('ProductionBatch', lazy='joined')
    creator = db.relationship('User', foreign_keys='StoreRequisition.created_by_id', lazy='joined')
    approver = db.relationship('User', foreign_keys='StoreRequisition.approved_by_id', lazy='joined')
    issuer = db.relationship('User', foreign_keys='StoreRequisition.issued_by_id', lazy='joined')


class StoreRequisitionItem(db.Model):
    __tablename__ = 'store_requisition_items'

    id = db.Column(db.Integer, primary_key=True)
    store_requisition_id = db.Column(db.Integer, db.ForeignKey('store_requisitions.id'), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    quantity_requested = db.Column(db.Numeric(12, 2), nullable=False)
    quantity_issued = db.Column(db.Numeric(12, 2), default=0)

    raw_material = db.relationship('RawMaterial', lazy='joined')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80))
    action = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
