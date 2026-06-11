from datetime import date
from decimal import Decimal
from typing import Optional

from models.models import (
    Invoice,
    Payment,
    SalesOrder,
    SalesQuotation,
    db,
)
from repositories.base import BaseRepository


class SalesQuotationRepository(BaseRepository[SalesQuotation]):
    def __init__(self) -> None:
        super().__init__(SalesQuotation)

    def get_by_quotation_number(self, quotation_number: str) -> Optional[SalesQuotation]:
        return SalesQuotation.query.filter_by(quotation_number=quotation_number).first()

    def get_by_customer(self, customer_id: int) -> list[SalesQuotation]:
        return SalesQuotation.query.filter_by(customer_id=customer_id).order_by(
            SalesQuotation.created_at.desc(),
        ).all()

    def get_by_status(self, status: str) -> list[SalesQuotation]:
        return SalesQuotation.query.filter_by(status=status).all()

    def get_by_branch(self, branch_id: int) -> list[SalesQuotation]:
        return SalesQuotation.query.filter_by(branch_id=branch_id).order_by(
            SalesQuotation.created_at.desc(),
        ).all()

    def get_active(self) -> list[SalesQuotation]:
        return SalesQuotation.query.filter(
            SalesQuotation.status.in_(['Draft', 'Sent', 'Accepted']),
        ).all()

    def get_expired(self) -> list[SalesQuotation]:
        from datetime import date
        return SalesQuotation.query.filter(
            SalesQuotation.valid_until < date.today(),
            SalesQuotation.status.in_(['Sent', 'Draft']),
        ).all()


class SalesOrderRepository(BaseRepository[SalesOrder]):
    def __init__(self) -> None:
        super().__init__(SalesOrder)

    def get_by_order_number(self, order_number: str) -> Optional[SalesOrder]:
        return SalesOrder.query.filter_by(order_number=order_number).first()

    def get_by_customer(self, customer_id: int) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(customer_id=customer_id).order_by(
            SalesOrder.order_date.desc(),
        ).all()

    def get_by_status(self, status: str) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(status=status).all()

    def get_by_branch(self, branch_id: int) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(branch_id=branch_id).order_by(
            SalesOrder.order_date.desc(),
        ).all()

    def get_by_warehouse(self, warehouse_id: int) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(warehouse_id=warehouse_id).order_by(
            SalesOrder.order_date.desc(),
        ).all()

    def get_by_quotation(self, quotation_id: int) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(quotation_id=quotation_id).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[SalesOrder]:
        return SalesOrder.query.filter(
            SalesOrder.order_date.between(start_date, end_date),
        ).all()

    def get_pending(self) -> list[SalesOrder]:
        return SalesOrder.query.filter(
            SalesOrder.status.in_(['Draft', 'Pending', 'Confirmed']),
        ).order_by(SalesOrder.order_date.asc()).all()

    def get_processing(self) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(status='Processing').all()

    def get_completed(self) -> list[SalesOrder]:
        return SalesOrder.query.filter_by(status='Completed').all()


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self) -> None:
        super().__init__(Invoice)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        return Invoice.query.filter_by(invoice_number=invoice_number).first()

    def get_by_customer(self, customer_id: int) -> list[Invoice]:
        return Invoice.query.filter_by(customer_id=customer_id).order_by(
            Invoice.invoice_date.desc(),
        ).all()

    def get_by_sales_order(self, sales_order_id: int) -> list[Invoice]:
        return Invoice.query.filter_by(sales_order_id=sales_order_id).all()

    def get_by_status(self, status: str) -> list[Invoice]:
        return Invoice.query.filter_by(status=status).all()

    def get_by_payment_status(self, payment_status: str) -> list[Invoice]:
        return Invoice.query.filter_by(payment_status=payment_status).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[Invoice]:
        return Invoice.query.filter(
            Invoice.invoice_date.between(start_date, end_date),
        ).all()

    def get_unpaid(self) -> list[Invoice]:
        return Invoice.query.filter(
            Invoice.payment_status.in_(['Unpaid', 'Partially Paid']),
            Invoice.status == 'Active',
        ).order_by(Invoice.due_date.asc()).all()

    def get_overdue(self) -> list[Invoice]:
        from datetime import date
        return Invoice.query.filter(
            Invoice.payment_status.in_(['Unpaid', 'Partially Paid']),
            Invoice.due_date < date.today(),
            Invoice.status == 'Active',
        ).order_by(Invoice.due_date.asc()).all()


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self) -> None:
        super().__init__(Payment)

    def get_by_payment_number(self, payment_number: str) -> Optional[Payment]:
        return Payment.query.filter_by(payment_number=payment_number).first()

    def get_by_invoice(self, invoice_id: int) -> list[Payment]:
        return Payment.query.filter_by(invoice_id=invoice_id).order_by(
            Payment.payment_date.desc(),
        ).all()

    def get_by_customer(self, customer_id: int) -> list[Payment]:
        return Payment.query.filter_by(customer_id=customer_id).order_by(
            Payment.payment_date.desc(),
        ).all()

    def get_by_method(self, payment_method: str) -> list[Payment]:
        return Payment.query.filter_by(payment_method=payment_method).order_by(
            Payment.payment_date.desc(),
        ).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[Payment]:
        return Payment.query.filter(
            Payment.payment_date.between(start_date, end_date),
        ).order_by(Payment.payment_date.desc()).all()

    def get_total_collected(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None,
    ) -> Decimal:
        query = Payment.query
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        total = query.with_entities(db.func.sum(Payment.amount)).scalar()
        return Decimal(str(total or 0))
