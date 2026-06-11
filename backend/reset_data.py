import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import create_app
from models.models import db, ProductCategory, Unit, Product, ProductionBatch, Warehouse, Customer
from models.models import Inventory, InventoryLedger, GoodsReceiveVoucher, GoodsIssueVoucher, Transfer
from models.models import SalesQuotation, SalesOrder, Invoice, Payment, AuditLog

app = create_app()
with app.app_context():
    print('Clearing transactional data...')

    Payment.query.delete()
    Invoice.query.delete()
    SalesOrder.query.delete()
    SalesQuotation.query.delete()
    GoodsIssueVoucher.query.delete()
    GoodsReceiveVoucher.query.delete()
    Transfer.query.delete()
    InventoryLedger.query.delete()
    Inventory.query.delete()
    ProductionBatch.query.delete()
    Customer.query.delete()
    Product.query.delete()
    Unit.query.delete()
    ProductCategory.query.delete()
    Warehouse.query.delete()
    AuditLog.query.delete()

    db.session.commit()
    print('Done. Users, roles, permissions, branches, and company preserved.')
