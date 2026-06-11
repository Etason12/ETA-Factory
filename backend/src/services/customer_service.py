from datetime import date
from typing import Any, Optional

from models.models import Customer, Invoice, Payment
from repositories.base import BaseRepository
from repositories.branch_repository import BranchRepository
from utils.error_handlers import ConflictError, NotFoundError, ValidationError
from utils.helpers import generate_code


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self) -> None:
        super().__init__(Customer)

    def get_by_code(self, code: str) -> Optional[Customer]:
        return Customer.query.filter(
            Customer.customer_code == code,
            Customer.is_deleted == False,
        ).first()

    def get_by_branch(self, branch_id: int) -> list[Customer]:
        return Customer.query.filter(
            Customer.branch_id == branch_id,
            Customer.is_deleted == False,
        ).all()

    def search(self, term: str) -> list[Customer]:
        pattern = f'%{term}%'
        return Customer.query.filter(
            Customer.is_deleted == False,
            (
                Customer.name.ilike(pattern) |
                Customer.phone.ilike(pattern) |
                Customer.email.ilike(pattern) |
                Customer.customer_code.ilike(pattern)
            ),
        ).all()


class CustomerService:
    def __init__(
        self,
        customer_repository: Optional[CustomerRepository] = None,
        branch_repository: Optional[BranchRepository] = None,
    ):
        self.repo = customer_repository or CustomerRepository()
        self.branch_repo = branch_repository or BranchRepository()

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError('Customer not found')
        return customer

    def get_customers(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        return self.repo.get_all(
            page=page, per_page=per_page, filters=filters, sort=sort, order=order
        )

    def _generate_customer_code(self) -> str:
        max_id = Customer.query.with_entities(Customer.id).order_by(Customer.id.desc()).first()
        next_seq = (max_id[0] + 1) if max_id else 1
        return generate_code('CUST', next_seq)

    def create_customer(
        self,
        name: str,
        branch_id: int,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        tin_number: Optional[str] = None,
        customer_type: str = 'Regular',
        credit_limit: float = 0,
    ) -> Customer:
        if not name or not name.strip():
            raise ValidationError('Customer name is required')

        branch = self.branch_repo.get_by_id(branch_id)
        if not branch:
            raise ValidationError('Branch not found')

        customer_code = self._generate_customer_code()

        customer = Customer(
            customer_code=customer_code,
            name=name.strip(),
            phone=phone,
            email=email,
            address=address,
            tin_number=tin_number,
            customer_type=customer_type,
            credit_limit=credit_limit,
            branch_id=branch_id,
            is_active=True,
        )
        return self.repo.create(customer)

    def update_customer(
        self,
        customer_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        tin_number: Optional[str] = None,
        customer_type: Optional[str] = None,
        credit_limit: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> Customer:
        customer = self.get_customer(customer_id)

        if name is not None:
            if not name.strip():
                raise ValidationError('Customer name cannot be empty')
            customer.name = name.strip()
        if phone is not None:
            customer.phone = phone
        if email is not None:
            customer.email = email
        if address is not None:
            customer.address = address
        if tin_number is not None:
            customer.tin_number = tin_number
        if customer_type is not None:
            customer.customer_type = customer_type
        if credit_limit is not None:
            customer.credit_limit = credit_limit
        if is_active is not None:
            customer.is_active = is_active

        return self.repo.update(customer)

    def delete_customer(self, customer_id: int) -> None:
        customer = self.get_customer(customer_id)
        self.repo.delete(customer)

    def get_customer_history(self, customer_id: int) -> dict[str, Any]:
        customer = self.get_customer(customer_id)

        invoices = Invoice.query.filter(
            Invoice.customer_id == customer_id,
            Invoice.status == 'Active',
        ).order_by(Invoice.invoice_date.desc()).all()

        payments = Payment.query.filter(
            Payment.customer_id == customer_id,
        ).order_by(Payment.payment_date.desc()).all()

        total_invoiced = sum(float(i.total_amount or 0) for i in invoices)
        total_paid = sum(float(p.amount or 0) for p in payments)
        balance = total_invoiced - total_paid

        return {
            'customer': {
                'id': customer.id,
                'code': customer.customer_code,
                'name': customer.name,
                'credit_limit': float(customer.credit_limit or 0),
            },
            'summary': {
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'balance': balance,
                'invoice_count': len(invoices),
                'payment_count': len(payments),
            },
            'recent_invoices': [
                {
                    'id': inv.id,
                    'invoice_number': inv.invoice_number,
                    'invoice_date': inv.invoice_date.isoformat(),
                    'total_amount': float(inv.total_amount or 0),
                    'balance_due': float(inv.balance_due or 0),
                    'payment_status': inv.payment_status,
                }
                for inv in invoices[:10]
            ],
            'recent_payments': [
                {
                    'id': p.id,
                    'payment_number': p.payment_number,
                    'payment_date': p.payment_date.isoformat(),
                    'amount': float(p.amount or 0),
                    'payment_method': p.payment_method,
                }
                for p in payments[:10]
            ],
        }
