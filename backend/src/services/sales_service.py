from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from models.models import (
    Customer,
    Invoice,
    LoadingAuthorization,
    Payment,
    SalesOrder,
    SalesOrderItem,
    SalesQuotation,
    SalesQuotationItem,
)
from repositories.base import BaseRepository
from repositories.branch_repository import BranchRepository
from services.inventory_service import InventoryService
from utils.error_handlers import NotFoundError, ValidationError


from sqlalchemy.orm import joinedload
# ... (imports)

class SalesQuotationRepository(BaseRepository[SalesQuotation]):
    def __init__(self) -> None:
        super().__init__(SalesQuotation)

    def get_all(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        query = self.model_class.query.options(joinedload(SalesQuotation.customer))
        if hasattr(self.model_class, 'is_deleted'):
            query = query.filter(self.model_class.is_deleted == False)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    column = getattr(self.model_class, key)
                    if isinstance(value, (list, tuple)):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        if sort and hasattr(self.model_class, sort):
            column = getattr(self.model_class, sort)
            query = query.order_by(desc(column) if order == 'desc' else asc(column))
        return paginate_helper(query, page, per_page)

class SalesOrderRepository(BaseRepository[SalesOrder]):
    def __init__(self) -> None:
        super().__init__(SalesOrder)

    def get_all(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        query = self.model_class.query.options(
            joinedload(SalesOrder.customer), 
            joinedload(SalesOrder.warehouse)
        )
        if hasattr(self.model_class, 'is_deleted'):
            query = query.filter(self.model_class.is_deleted == False)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    column = getattr(self.model_class, key)
                    if isinstance(value, (list, tuple)):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        if sort and hasattr(self.model_class, sort):
            column = getattr(self.model_class, sort)
            query = query.order_by(desc(column) if order == 'desc' else asc(column))
        return paginate_helper(query, page, per_page)



class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self) -> None:
        super().__init__(Invoice)


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self) -> None:
        super().__init__(Payment)


class LoadingAuthorizationRepository(BaseRepository[LoadingAuthorization]):
    def __init__(self) -> None:
        super().__init__(LoadingAuthorization)


class SalesService:
    def __init__(
        self,
        quotation_repo: Optional[SalesQuotationRepository] = None,
        order_repo: Optional[SalesOrderRepository] = None,
        invoice_repo: Optional[InvoiceRepository] = None,
        payment_repo: Optional[PaymentRepository] = None,
        loading_auth_repo: Optional[LoadingAuthorizationRepository] = None,
        inventory_service: Optional[InventoryService] = None,
        branch_repository: Optional[BranchRepository] = None,
    ):
        self.quotation_repo = quotation_repo or SalesQuotationRepository()
        self.order_repo = order_repo or SalesOrderRepository()
        self.invoice_repo = invoice_repo or InvoiceRepository()
        self.payment_repo = payment_repo or PaymentRepository()
        self.loading_auth_repo = loading_auth_repo or LoadingAuthorizationRepository()
        self.inventory_service = inventory_service or InventoryService()
        self.branch_repo = branch_repository or BranchRepository()

    # ─── Quotations ───────────────────────────────────────────────────────

    def create_quotation(
        self,
        customer_id: int,
        branch_id: int,
        items: list[dict[str, Any]],
        valid_until: Optional[date] = None,
        notes: Optional[str] = None,
        tax_amount: Optional[float] = None,
        created_by_id: Optional[int] = None,
    ) -> SalesQuotation:
        customer = Customer.query.get(customer_id)
        if not customer:
            raise ValidationError('Customer not found')

        branch = self.branch_repo.get_by_id(branch_id)
        if not branch:
            raise ValidationError('Branch not found')

        if not items:
            raise ValidationError('At least one item is required')

        today = date.today()
        count = SalesQuotation.query.filter(
            SalesQuotation.created_at >= datetime(today.year, today.month, today.day)
        ).count() + 1
        quotation_number = f'QTN-{today.strftime("%Y%m%d")}-{count:05d}'

        subtotal = Decimal(0)
        quotation_items = []
        for item_data in items:
            product_id = item_data['product_id']
            quantity = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data.get('unit_price', 0)))
            total_price = quantity * unit_price
            subtotal += total_price

            quotation_items.append({
                'product_id': product_id,
                'quantity': float(quantity),
                'unit_price': float(unit_price),
                'total_price': float(total_price),
            })

        # Dynamic tax: Use provided tax_amount or Company default
        if tax_amount is not None:
            final_tax = Decimal(str(tax_amount))
        else:
            company = Company.query.filter_by(is_active=True).first()
            tax_rate = Decimal(str(company.default_tax_rate)) if company else Decimal('0')
            final_tax = subtotal * tax_rate

        total_amount = subtotal + final_tax

        quotation = SalesQuotation(
            quotation_number=quotation_number,
            customer_id=customer_id,
            branch_id=branch_id,
            status='Draft',
            valid_until=valid_until,
            subtotal=float(subtotal),
            tax_amount=float(final_tax),
            total_amount=float(total_amount),
            notes=notes,
            created_by_id=created_by_id,
        )
        quotation = self.quotation_repo.create(quotation)

        from models.models import db

        for i in quotation_items:
            item = SalesQuotationItem(
                quotation_id=quotation.id,
                product_id=i['product_id'],
                quantity=i['quantity'],
                unit_price=i['unit_price'],
                total_price=i['total_price'],
            )
            db.session.add(item)
        db.session.commit()

        return self.quotation_repo.get_by_id(quotation.id)

    def get_quotation(self, quotation_id: int) -> SalesQuotation:
        q = self.quotation_repo.get_by_id(quotation_id)
        if not q:
            raise NotFoundError('Quotation not found')
        return q

    def get_quotations(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        return self.quotation_repo.get_all(
            page=page, per_page=per_page, filters=filters, sort=sort, order=order
        )

    # ─── Orders ───────────────────────────────────────────────────────────

    def convert_to_order(
        self,
        quotation_id: int,
        warehouse_id: int,
        order_date: Optional[date] = None,
        created_by_id: Optional[int] = None,
    ) -> SalesOrder:
        quotation = self.get_quotation(quotation_id)

        if quotation.status != 'Draft':
            raise ValidationError(f'Cannot convert quotation with status {quotation.status}')

        today = order_date or date.today()
        count = SalesOrder.query.filter(
            SalesOrder.created_at >= datetime(today.year, today.month, today.day)
        ).count() + 1
        order_number = f'ORD-{today.strftime("%Y%m%d")}-{count:05d}'

        order = SalesOrder(
            order_number=order_number,
            customer_id=quotation.customer_id,
            branch_id=quotation.branch_id,
            warehouse_id=warehouse_id,
            quotation_id=quotation_id,
            order_date=today,
            status='Draft',
            subtotal=quotation.subtotal,
            tax_amount=quotation.tax_amount,
            total_amount=quotation.total_amount,
            notes=quotation.notes,
        )
        order = self.order_repo.create(order)

        from models.models import db

        for qi in quotation.items:
            soi = SalesOrderItem(
                sales_order_id=order.id,
                product_id=qi.product_id,
                quantity=qi.quantity,
                unit_price=qi.unit_price,
                total_price=qi.total_price,
            )
            db.session.add(soi)

        quotation.status = 'Converted'
        db.session.commit()

        return self.order_repo.get_by_id(order.id)

    def create_order(
        self,
        customer_id: int,
        branch_id: int,
        warehouse_id: int,
        items: list[dict[str, Any]],
        order_date: Optional[date] = None,
        notes: Optional[str] = None,
        tax_amount: Optional[float] = None,
        created_by_id: Optional[int] = None,
    ) -> SalesOrder:
        customer = Customer.query.get(customer_id)
        if not customer:
            raise ValidationError('Customer not found')

        if not items:
            raise ValidationError('At least one order item is required')

        today = order_date or date.today()
        count = SalesOrder.query.filter(
            SalesOrder.created_at >= datetime(today.year, today.month, today.day)
        ).count() + 1
        order_number = f'ORD-{today.strftime("%Y%m%d")}-{count:05d}'

        subtotal = Decimal(0)
        order_items = []
        for item_data in items:
            product_id = item_data['product_id']
            # We no longer pre-calculate cost_price here, it will be determined at fulfillment
            
            quantity = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data.get('unit_price', 0)))
            total_price = quantity * unit_price
            subtotal += total_price

            order_items.append({
                'product_id': product_id,
                'quantity': float(quantity),
                'unit_price': float(unit_price),
                'total_price': float(total_price),
                'cost_price': 0.0  # Placeholder, will be updated at fulfillment
            })

        # Dynamic tax
        if tax_amount is not None:
            final_tax = Decimal(str(tax_amount))
        else:
            company = Company.query.filter_by(is_active=True).first()
            tax_rate = Decimal(str(company.default_tax_rate)) if company else Decimal('0')
            final_tax = subtotal * tax_rate

        total_amount = subtotal + final_tax

        order = SalesOrder(
            order_number=order_number,
            customer_id=customer_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            order_date=today,
            status='Draft',
            subtotal=float(subtotal),
            tax_amount=float(final_tax),
            total_amount=float(total_amount),
            notes=notes,
            created_by_id=created_by_id,
        )
        order = self.order_repo.create(order)

        from models.models import db

        for i in order_items:
            item = SalesOrderItem(
                sales_order_id=order.id,
                product_id=i['product_id'],
                quantity=i['quantity'],
                unit_price=i['unit_price'],
                total_price=i['total_price'],
                cost_price=i['cost_price']
            )
            db.session.add(item)
        db.session.commit()

        return self.order_repo.get_by_id(order.id)

    def get_order(self, order_id: int) -> SalesOrder:
        o = self.order_repo.get_by_id(order_id)
        if not o:
            raise NotFoundError('Sales order not found')
        return o

    def get_orders(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        return self.order_repo.get_all(
            page=page, per_page=per_page, filters=filters, sort=sort, order=order
        )

    def approve_order(
        self,
        order_id: int,
        approved_by_id: int,
    ) -> SalesOrder:
        order = self.get_order(order_id)

        if order.status != 'Draft':
            raise ValidationError(f'Order is already {order.status}')

        for item in order.items:
            self.inventory_service.reserve_stock(
                product_id=item.product_id,
                warehouse_id=order.warehouse_id,
                quantity=float(item.quantity),
            )

        order.status = 'Approved'
        order.approved_by_id = approved_by_id
        order.approved_at = datetime.utcnow()
        return self.order_repo.update(order)

    # ─── Loading Authorization ────────────────────────────────────────────

    def create_loading_authorization(
        self,
        sales_order_id: int,
        authorized_by_id: int,
        notes: Optional[str] = None,
    ) -> LoadingAuthorization:
        order = self.get_order(sales_order_id)

        if order.status != 'Approved':
            raise ValidationError('Order must be approved before loading authorization')

        today = date.today()
        count = LoadingAuthorization.query.filter(
            LoadingAuthorization.created_at >= datetime(today.year, today.month, today.day)
        ).count() + 1
        auth_number = f'LA-{today.strftime("%Y%m%d")}-{count:05d}'

        auth = LoadingAuthorization(
            authorization_number=auth_number,
            sales_order_id=sales_order_id,
            warehouse_id=order.warehouse_id,
            authorized_date=today,
            status='Approved',
            authorized_by_id=authorized_by_id,
            notes=notes,
        )
        auth = self.loading_auth_repo.create(auth)

        order.status = 'Loading Authorized'
        self.order_repo.update(order)

        giv = self.inventory_service.create_goods_issue_voucher(
            warehouse_id=order.warehouse_id,
            items=[
                {
                    'product_id': item.product_id,
                    'quantity': float(item.quantity),
                }
                for item in order.items
            ],
            sales_order_id=order.id,
            reference_type='LoadingAuthorization',
            reference_id=auth.id,
            notes=f'Auto-generated GIV for loading auth {auth.authorization_number}',
            created_by_id=authorized_by_id,
            issued_by_id=authorized_by_id,
        )

        self.inventory_service.process_goods_issue(giv.id, authorized_by_id)

        order.status = 'Goods Issued'
        self.order_repo.update(order)

        return auth

    # ─── Invoices ─────────────────────────────────────────────────────────

    def create_invoice(
        self,
        sales_order_id: int,
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Invoice:
        order = self.get_order(sales_order_id)

        today = invoice_date or date.today()
        count = Invoice.query.filter(
            Invoice.created_at >= datetime(today.year, today.month, today.day)
        ).count() + 1
        invoice_number = f'INV-{today.strftime("%Y%m%d")}-{count:05d}'

        invoice = Invoice(
            invoice_number=invoice_number,
            sales_order_id=order.id,
            customer_id=order.customer_id,
            invoice_date=today,
            due_date=due_date or today,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            paid_amount=0,
            balance_due=order.total_amount,
            payment_status='Unpaid',
            status='Active',
            notes=notes,
        )
        return self.invoice_repo.create(invoice)

    def get_invoice(self, invoice_id: int) -> Invoice:
        inv = self.invoice_repo.get_by_id(invoice_id)
        if not inv:
            raise NotFoundError('Invoice not found')
        return inv

    def get_invoices(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        return self.invoice_repo.get_all(
            page=page, per_page=per_page, filters=filters, sort=sort, order=order
        )

    # ─── Payments ─────────────────────────────────────────────────────────

    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_method: str,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        received_by_id: Optional[int] = None,
    ) -> Invoice:
        invoice = self.get_invoice(invoice_id)

        if invoice.payment_status == 'Paid':
            raise ValidationError('Invoice is already fully paid')

        if amount <= 0:
            raise ValidationError('Payment amount must be positive')

        today = payment_date or date.today()
        count = Payment.query.filter(
            Payment.created_at >= datetime(today.year, today.month, today.day)
        ).count() + 1
        payment_number = f'PAY-{today.strftime("%Y%m%d")}-{count:05d}'

        payment = Payment(
            payment_number=payment_number,
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            amount=amount,
            payment_date=today,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            received_by_id=received_by_id,
        )
        self.payment_repo.create(payment)

        total_paid = float(invoice.paid_amount or 0) + amount
        balance = float(invoice.total_amount or 0) - total_paid

        invoice.paid_amount = total_paid
        invoice.balance_due = max(0, balance)
        invoice.payment_status = 'Paid' if balance <= 0 else 'Partial'
        self.invoice_repo.update(invoice)

        return invoice
