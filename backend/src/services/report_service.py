from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import Date, cast, func

from models.models import (
    AuditLog,
    Branch,
    Customer,
    GoodsIssueVoucher,
    GoodsReceiveVoucher,
    Inventory,
    InventoryLedger,
    Invoice,
    Payment,
    ProductionBatch,
    Product,
    SalesOrder,
    SalesOrderItem,
    Transfer,
    User,
    Warehouse,
)


class ReportService:
    def _to_date_range(
        self, start_date: Optional[date], end_date: Optional[date]
    ) -> tuple[date, date]:
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        return start_date, end_date

    # ─── Sales Reports ────────────────────────────────────────────────────

    def daily_sales_report(
        self, report_date: Optional[date] = None
    ) -> dict[str, Any]:
        report_date = report_date or date.today()

        invoices = Invoice.query.filter(
            Invoice.invoice_date == report_date,
            Invoice.status == 'Active',
        ).all()

        total_sales = sum(float(i.total_amount or 0) for i in invoices)
        total_paid = sum(float(i.paid_amount or 0) for i in invoices)
        outstanding = total_sales - total_paid

        return {
            'report_date': report_date.isoformat(),
            'report_type': 'daily_sales',
            'summary': {
                'total_invoices': len(invoices),
                'total_sales': total_sales,
                'total_paid': total_paid,
                'outstanding': outstanding,
            },
            'invoices': [
                {
                    'invoice_number': inv.invoice_number,
                    'customer_name': inv.customer.name if inv.customer else None,
                    'total_amount': float(inv.total_amount or 0),
                    'paid_amount': float(inv.paid_amount or 0),
                    'balance_due': float(inv.balance_due or 0),
                    'payment_status': inv.payment_status,
                }
                for inv in invoices
            ],
        }

    def monthly_sales_report(
        self, year: int, month: int
    ) -> dict[str, Any]:
        invoices = Invoice.query.filter(
            cast(Invoice.invoice_date, Date) >= date(year, month, 1),
            cast(Invoice.invoice_date, Date) < (
                date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
            ),
            Invoice.status == 'Active',
        ).all()

        total_sales = sum(float(i.total_amount or 0) for i in invoices)
        total_paid = sum(float(i.paid_amount or 0) for i in invoices)
        outstanding = total_sales - total_paid

        return {
            'year': year,
            'month': month,
            'report_type': 'monthly_sales',
            'summary': {
                'total_invoices': len(invoices),
                'total_sales': total_sales,
                'total_paid': total_paid,
                'outstanding': outstanding,
            },
            'invoices': [
                {
                    'invoice_number': inv.invoice_number,
                    'invoice_date': inv.invoice_date.isoformat(),
                    'customer_name': inv.customer.name if inv.customer else None,
                    'total_amount': float(inv.total_amount or 0),
                    'paid_amount': float(inv.paid_amount or 0),
                    'balance_due': float(inv.balance_due or 0),
                    'payment_status': inv.payment_status,
                }
                for inv in invoices
            ],
        }

    # ─── Inventory Reports ────────────────────────────────────────────────

    def inventory_valuation(self) -> dict[str, Any]:
        from sqlalchemy import func as sa_func

        products = Product.query.filter(Product.is_deleted == False).all()
        total_value = 0
        product_data = []

        for product in products:
            inventory_records = Inventory.query.filter(
                Inventory.product_id == product.id
            ).all()

            total_qty = sum(float(r.quantity_on_hand or 0) for r in inventory_records)
            avg_cost = float(product.cost_price or 0)
            value = total_qty * avg_cost
            total_value += value

            if total_qty > 0:
                product_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku': product.sku,
                    'total_quantity': total_qty,
                    'average_cost': avg_cost,
                    'valuation': value,
                })

        return {
            'report_type': 'inventory_valuation',
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_products': len(product_data),
                'total_quantity': sum(p['total_quantity'] for p in product_data),
                'total_valuation': total_value,
            },
            'products': sorted(product_data, key=lambda x: x['valuation'], reverse=True),
        }

    def inventory_movement(
        self,
        product_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        start_date, end_date = self._to_date_range(start_date, end_date)

        query = InventoryLedger.query.filter(
            InventoryLedger.transaction_date >= datetime.combine(start_date, datetime.min.time()),
            InventoryLedger.transaction_date <= datetime.combine(end_date, datetime.max.time()),
        )

        if product_id:
            query = query.filter(InventoryLedger.product_id == product_id)
        if warehouse_id:
            query = query.filter(InventoryLedger.warehouse_id == warehouse_id)

        query = query.order_by(InventoryLedger.transaction_date.desc())

        from utils.helpers import paginate
        result = paginate(query, page, per_page)

        return {
            'report_type': 'inventory_movement',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'items': [
                {
                    'id': entry.id,
                    'product_name': entry.product.name if entry.product else None,
                    'warehouse_name': entry.warehouse.name if entry.warehouse else None,
                    'movement_type': entry.movement_type,
                    'quantity': float(entry.quantity or 0),
                    'unit_cost': float(entry.unit_cost or 0),
                    'reference_type': entry.reference_type,
                    'reference_id': entry.reference_id,
                    'batch_number': entry.batch_number,
                    'transaction_date': entry.transaction_date.isoformat(),
                }
                for entry in result['items']
            ],
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        }

    # ─── Branch Performance ──────────────────────────────────────────────

    def branch_performance(
        self,
        branch_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, Any]:
        start_date, end_date = self._to_date_range(start_date, end_date)

        query = Invoice.query.filter(
            Invoice.invoice_date >= start_date,
            Invoice.invoice_date <= end_date,
            Invoice.status == 'Active',
        )

        branches_query = Branch.query.filter(Branch.is_deleted == False)
        if branch_id:
            branches_query = branches_query.filter(Branch.id == branch_id)

        branches = branches_query.all()
        branch_data = []

        for branch in branches:
            branch_invoices = query.filter(
                Invoice.customer_id.in_(
                    Customer.query.with_entities(Customer.id).filter(
                        Customer.branch_id == branch.id
                    )
                )
            ).all() if branch.id else []

            total_sales = sum(float(i.total_amount or 0) for i in branch_invoices)
            total_paid = sum(float(i.paid_amount or 0) for i in branch_invoices)

            branch_data.append({
                'branch_id': branch.id,
                'branch_name': branch.name,
                'total_invoices': len(branch_invoices),
                'total_sales': total_sales,
                'total_paid': total_paid,
                'outstanding': total_sales - total_paid,
            })

        return {
            'report_type': 'branch_performance',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'branches': branch_data,
            'summary': {
                'total_sales': sum(b['total_sales'] for b in branch_data),
                'total_paid': sum(b['total_paid'] for b in branch_data),
                'total_outstanding': sum(b['outstanding'] for b in branch_data),
            },
        }

    def warehouse_stock(
        self, warehouse_id: Optional[int] = None
    ) -> dict[str, Any]:
        query = Inventory.query

        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)

        records = query.all()
        warehouse_groups: dict[int, dict[str, Any]] = {}

        for rec in records:
            wid = rec.warehouse_id
            if wid not in warehouse_groups:
                warehouse_groups[wid] = {
                    'warehouse_id': wid,
                    'warehouse_name': rec.warehouse.name if rec.warehouse else None,
                    'total_products': 0,
                    'total_quantity': 0,
                    'total_value': 0,
                    'items': [],
                }

            g = warehouse_groups[wid]
            qty = float(rec.quantity_on_hand or 0)
            cost = float(rec.product.cost_price or 0) if rec.product else 0
            g['total_products'] += 1
            g['total_quantity'] += qty
            g['total_value'] += qty * cost
            g['items'].append({
                'product_id': rec.product_id,
                'product_name': rec.product.name if rec.product else None,
                'sku': rec.product.sku if rec.product else None,
                'quantity_on_hand': qty,
                'reserved_quantity': float(rec.reserved_quantity or 0),
                'available_quantity': float(rec.available_quantity),
                'unit_cost': cost,
                'valuation': qty * cost,
            })

        return {
            'report_type': 'warehouse_stock',
            'generated_at': datetime.utcnow().isoformat(),
            'warehouses': list(warehouse_groups.values()),
        }

    # ─── Production Reports ──────────────────────────────────────────────

    def production_reports(
        self,
        product_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        start_date, end_date = self._to_date_range(start_date, end_date)

        query = ProductionBatch.query.filter(
            ProductionBatch.production_date >= start_date,
            ProductionBatch.production_date <= end_date,
        )

        if product_id:
            query = query.filter(ProductionBatch.product_id == product_id)
        if status:
            query = query.filter(ProductionBatch.status == status)

        query = query.order_by(ProductionBatch.production_date.desc())

        from utils.helpers import paginate
        result = paginate(query, page, per_page)

        total_cost = sum(float(b.production_cost or 0) for b in result['items'])
        total_qty = sum(float(b.quantity_produced or 0) for b in result['items'])

        return {
            'report_type': 'production',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'batches': [
                {
                    'batch_number': b.batch_number,
                    'product_name': b.product.name if b.product else None,
                    'quantity_produced': float(b.quantity_produced or 0),
                    'production_cost': float(b.production_cost or 0),
                    'unit_cost': (
                        float(b.production_cost) / float(b.quantity_produced)
                        if float(b.quantity_produced) > 0
                        else 0
                    ),
                    'production_date': b.production_date.isoformat(),
                    'warehouse_name': b.warehouse.name if b.warehouse else None,
                    'status': b.status,
                    'created_at': b.created_at.isoformat() if b.created_at else None,
                }
                for b in result['items']
            ],
            'summary': {
                'total_batches': result['total'],
                'total_quantity': total_qty,
                'total_cost': total_cost,
            },
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        }

    # ─── Customer Balance ────────────────────────────────────────────────

    def customer_balance(
        self,
        customer_id: Optional[int] = None,
        branch_id: Optional[int] = None,
    ) -> dict[str, Any]:
        customer_query = Customer.query.filter(Customer.is_deleted == False)

        if customer_id:
            customer_query = customer_query.filter(Customer.id == customer_id)
        if branch_id:
            customer_query = customer_query.filter(Customer.branch_id == branch_id)

        customers = customer_query.all()
        customer_data = []

        for customer in customers:
            invoices = Invoice.query.filter(
                Invoice.customer_id == customer.id,
                Invoice.status == 'Active',
            ).all()

            total_invoiced = sum(float(i.total_amount or 0) for i in invoices)
            total_paid = sum(float(i.paid_amount or 0) for i in invoices)
            balance = total_invoiced - total_paid

            customer_data.append({
                'customer_id': customer.id,
                'customer_code': customer.customer_code,
                'customer_name': customer.name,
                'credit_limit': float(customer.credit_limit or 0),
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'balance': balance,
                'available_credit': max(0, float(customer.credit_limit or 0) - balance),
                'invoice_count': len(invoices),
            })

        return {
            'report_type': 'customer_balance',
            'generated_at': datetime.utcnow().isoformat(),
            'customers': sorted(
                customer_data, key=lambda x: x['balance'], reverse=True
            ),
            'summary': {
                'total_customers': len(customer_data),
                'total_outstanding': sum(c['balance'] for c in customer_data),
                'total_credit_limit': sum(c['credit_limit'] for c in customer_data),
            },
        }

    # ─── Transfer Reports ────────────────────────────────────────────────

    def transfer_reports(
        self,
        source_warehouse_id: Optional[int] = None,
        destination_warehouse_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        start_date, end_date = self._to_date_range(start_date, end_date)

        query = Transfer.query.filter(
            Transfer.transfer_date >= start_date,
            Transfer.transfer_date <= end_date,
        )

        if source_warehouse_id:
            query = query.filter(Transfer.source_warehouse_id == source_warehouse_id)
        if destination_warehouse_id:
            query = query.filter(
                Transfer.destination_warehouse_id == destination_warehouse_id
            )
        if status:
            query = query.filter(Transfer.status == status)

        query = query.order_by(Transfer.transfer_date.desc())

        from utils.helpers import paginate
        result = paginate(query, page, per_page)

        return {
            'report_type': 'transfer',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'transfers': [
                {
                    'transfer_number': t.transfer_number,
                    'source_warehouse': t.source_warehouse.name if t.source_warehouse else None,
                    'destination_warehouse': t.destination_warehouse.name if t.destination_warehouse else None,
                    'transfer_date': t.transfer_date.isoformat(),
                    'status': t.status,
                    'item_count': t.items.count(),
                    'total_quantity': sum(
                        float(i.quantity or 0) for i in t.items
                    ),
                    'requested_by': t.requested_by_id,
                    'approved_by': t.approved_by_id,
                }
                for t in result['items']
            ],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        }
