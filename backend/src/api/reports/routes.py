from flask import jsonify, request
from flask_jwt_extended import jwt_required
from models.models import (
    SalesOrder, SalesOrderItem, Invoice, Payment,
    Inventory, InventoryLedger, Product, Customer,
    ProductionBatch, Transfer, Branch, Warehouse, db
)
from utils.error_handlers import ValidationError
from api.decorators import permission_required
from . import reports_bp
from datetime import date, datetime


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError(f'Invalid date format: {date_str}. Use YYYY-MM-DD')


@reports_bp.route('/daily-sales', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def daily_sales_report():
    report_date = request.args.get('date', date.today().isoformat())
    branch_id = request.args.get('branch_id', type=int)
    parsed_date = parse_date(report_date)

    query = SalesOrder.query.filter(
        db.func.date(SalesOrder.order_date) == parsed_date,
        SalesOrder.status.in_(['Approved', 'Completed'])
    )

    if branch_id:
        query = query.filter(SalesOrder.branch_id == branch_id)

    orders = query.all()

    total_sales = sum(float(o.total_amount or 0) for o in orders)
    total_orders = len(orders)

    return jsonify({
        'report_type': 'daily-sales',
        'date': report_date,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'orders': [{
            'id': o.id, 'order_number': o.order_number,
            'customer_name': o.customer.name if o.customer else None,
            'total_amount': float(o.total_amount or 0),
        } for o in orders],
    }), 200


@reports_bp.route('/monthly-sales', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def monthly_sales_report():
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)
    branch_id = request.args.get('branch_id', type=int)

    query = SalesOrder.query.filter(
        db.extract('year', SalesOrder.order_date) == year,
        db.extract('month', SalesOrder.order_date) == month,
        SalesOrder.status.in_(['Approved', 'Completed'])
    )

    if branch_id:
        query = query.filter(SalesOrder.branch_id == branch_id)

    orders = query.all()

    total_sales = sum(float(o.total_amount or 0) for o in orders)
    total_orders = len(orders)

    daily_breakdown = {}
    for o in orders:
        day = o.order_date.day if o.order_date else 0
        daily_breakdown[day] = daily_breakdown.get(day, 0) + float(o.total_amount or 0)

    return jsonify({
        'report_type': 'monthly-sales',
        'year': year,
        'month': month,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'daily_breakdown': [{'day': d, 'sales': s} for d, s in sorted(daily_breakdown.items())],
    }), 200


@reports_bp.route('/inventory-valuation', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def inventory_valuation():
    warehouse_id = request.args.get('warehouse_id', type=int)

    query = Inventory.query

    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)

    inventory = query.all()

    total_value = 0
    items = []
    for inv in inventory:
        if inv.product and inv.product.cost_price:
            value = float(inv.quantity_on_hand or 0) * float(inv.product.cost_price)
            total_value += value
            items.append({
                'product_id': inv.product_id,
                'product_name': inv.product.name,
                'product_sku': inv.product.sku,
                'quantity': float(inv.quantity_on_hand or 0),
                'cost_price': float(inv.product.cost_price),
                'value': value,
                'warehouse_name': inv.warehouse.name if inv.warehouse else None,
            })

    return jsonify({
        'report_type': 'inventory-valuation',
        'total_value': total_value,
        'items': items,
    }), 200


@reports_bp.route('/inventory-movement', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def inventory_movement():
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = InventoryLedger.query

    if product_id:
        query = query.filter(InventoryLedger.product_id == product_id)
    if warehouse_id:
        query = query.filter(InventoryLedger.warehouse_id == warehouse_id)
    if date_from:
        query = query.filter(InventoryLedger.transaction_date >= parse_date(date_from))
    if date_to:
        query = query.filter(InventoryLedger.transaction_date <= parse_date(date_to))

    entries = query.order_by(InventoryLedger.transaction_date.desc()).limit(500).all()

    total_in = sum(float(e.quantity or 0) for e in entries if float(e.quantity or 0) > 0)
    total_out = sum(abs(float(e.quantity or 0)) for e in entries if float(e.quantity or 0) < 0)

    return jsonify({
        'report_type': 'inventory-movement',
        'total_in': total_in,
        'total_out': total_out,
        'entries': [{
            'id': e.id, 'product_name': e.product.name if e.product else None,
            'product_sku': e.product.sku if e.product else None,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'movement_type': e.movement_type,
            'quantity': float(e.quantity or 0),
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        } for e in entries],
    }), 200


@reports_bp.route('/branch-performance', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def branch_performance():
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)

    branches = Branch.query.filter(Branch.is_deleted == False).all()

    performance = []
    for branch in branches:
        orders = SalesOrder.query.filter(
            SalesOrder.branch_id == branch.id,
            db.extract('year', SalesOrder.order_date) == year,
            db.extract('month', SalesOrder.order_date) == month,
            SalesOrder.status.in_(['Approved', 'Completed'])
        ).all()

        total_sales = sum(float(o.total_amount or 0) for o in orders)
        total_orders = len(orders)
        total_customers = len(set(o.customer_id for o in orders if o.customer_id))

        invoices = Invoice.query.filter(
            Invoice.customer_id.in_(
                db.session.query(SalesOrder.customer_id).filter(
                    SalesOrder.branch_id == branch.id,
                    db.extract('year', SalesOrder.order_date) == year,
                    db.extract('month', SalesOrder.order_date) == month,
                )
            )
        ).all()
        total_collected = sum(float(i.paid_amount or 0) for i in invoices)

        performance.append({
            'branch_id': branch.id,
            'branch_name': branch.name,
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_customers': total_customers,
            'total_collected': total_collected,
        })

    return jsonify({
        'report_type': 'branch-performance',
        'year': year,
        'month': month,
        'branches': performance,
    }), 200


@reports_bp.route('/warehouse-stock', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def warehouse_stock():
    warehouse_id = request.args.get('warehouse_id', type=int)
    branch_id = request.args.get('branch_id', type=int)

    query = Warehouse.query.filter(Warehouse.is_deleted == False)

    if branch_id:
        query = query.filter(Warehouse.branch_id == branch_id)

    warehouses = query.all()

    result = []
    for wh in warehouses:
        if warehouse_id and wh.id != warehouse_id:
            continue
        inv_query = Inventory.query.filter_by(warehouse_id=wh.id)
        items = inv_query.all()
        total_items = len(items)
        total_qty = sum(float(i.quantity_on_hand or 0) for i in items)
        total_value = sum(
            float(i.quantity_on_hand or 0) * float(i.product.cost_price or 0)
            for i in items if i.product
        )

        result.append({
            'warehouse_id': wh.id,
            'warehouse_name': wh.name,
            'warehouse_code': wh.code,
            'branch_name': wh.branch.name if wh.branch else None,
            'total_items': total_items,
            'total_quantity': total_qty,
            'total_value': total_value,
        })

    return jsonify({
        'report_type': 'warehouse-stock',
        'warehouses': result,
    }), 200


@reports_bp.route('/production', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def production_report():
    product_id = request.args.get('product_id', type=int)
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = ProductionBatch.query

    if product_id:
        query = query.filter(ProductionBatch.product_id == product_id)
    if date_from:
        query = query.filter(ProductionBatch.production_date >= parse_date(date_from))
    if date_to:
        query = query.filter(ProductionBatch.production_date <= parse_date(date_to))

    batches = query.order_by(ProductionBatch.production_date.desc()).all()

    total_produced = sum(float(b.quantity_produced or 0) for b in batches)
    total_cost = sum(float(b.production_cost or 0) for b in batches)
    total_batches = len(batches)
    approved_batches = sum(1 for b in batches if b.status == 'Approved')

    return jsonify({
        'report_type': 'production',
        'total_batches': total_batches,
        'approved_batches': approved_batches,
        'total_quantity_produced': total_produced,
        'total_production_cost': total_cost,
        'batches': [{
            'id': b.id, 'batch_number': b.batch_number,
            'product_name': b.product.name if b.product else None,
            'quantity_produced': float(b.quantity_produced or 0),
            'production_cost': float(b.production_cost or 0),
            'production_date': b.production_date.isoformat() if b.production_date else None,
            'status': b.status,
        } for b in batches],
    }), 200


@reports_bp.route('/customer-balances', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def customer_balances():
    branch_id = request.args.get('branch_id', type=int)

    query = Customer.query.filter(Customer.is_deleted == False)

    if branch_id:
        query = query.filter(Customer.branch_id == branch_id)

    customers = query.order_by(Customer.name.asc()).all()

    balances = []
    for c in customers:
        invoices = Invoice.query.filter_by(customer_id=c.id).all()
        total_invoiced = sum(float(i.total_amount or 0) for i in invoices)
        total_paid = sum(float(i.paid_amount or 0) for i in invoices)
        balance = total_invoiced - total_paid

        balances.append({
            'customer_id': c.id,
            'customer_name': c.name,
            'customer_code': c.customer_code,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'balance': balance,
        })

    total_balance = sum(b['balance'] for b in balances)

    return jsonify({
        'report_type': 'customer-balances',
        'total_balance': total_balance,
        'customers': balances,
    }), 200


@reports_bp.route('/transfers', methods=['GET'])
@jwt_required()
@permission_required('reports.view')
def transfer_report():
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    source_warehouse_id = request.args.get('source_warehouse_id', type=int)
    destination_warehouse_id = request.args.get('destination_warehouse_id', type=int)
    status = request.args.get('status', '').strip()

    query = Transfer.query

    if date_from:
        query = query.filter(Transfer.transfer_date >= parse_date(date_from))
    if date_to:
        query = query.filter(Transfer.transfer_date <= parse_date(date_to))
    if source_warehouse_id:
        query = query.filter(Transfer.source_warehouse_id == source_warehouse_id)
    if destination_warehouse_id:
        query = query.filter(Transfer.destination_warehouse_id == destination_warehouse_id)
    if status:
        query = query.filter(Transfer.status == status)

    transfers = query.order_by(Transfer.transfer_date.desc()).limit(500).all()

    return jsonify({
        'report_type': 'transfers',
        'total_transfers': len(transfers),
        'transfers': [{
            'id': t.id, 'transfer_number': t.transfer_number,
            'source_warehouse_name': t.source_warehouse.name if t.source_warehouse else None,
            'destination_warehouse_name': t.destination_warehouse.name if t.destination_warehouse else None,
            'transfer_date': t.transfer_date.isoformat() if t.transfer_date else None,
            'status': t.status,
        } for t in transfers],
    }), 200
