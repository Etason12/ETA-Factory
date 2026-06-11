from typing import Optional

from models.models import Customer
from repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self) -> None:
        super().__init__(Customer)

    def get_by_code(self, code: str) -> Optional[Customer]:
        return Customer.query.filter(
            Customer.customer_code == code,
            Customer.is_deleted == False,
        ).first()

    def get_by_name(self, name: str) -> list[Customer]:
        pattern = f'%{name}%'
        return Customer.query.filter(
            Customer.name.ilike(pattern),
            Customer.is_deleted == False,
        ).all()

    def get_by_branch(self, branch_id: int) -> list[Customer]:
        return Customer.query.filter(
            Customer.branch_id == branch_id,
            Customer.is_deleted == False,
        ).all()

    def get_by_type(self, customer_type: str) -> list[Customer]:
        return Customer.query.filter(
            Customer.customer_type == customer_type,
            Customer.is_deleted == False,
        ).all()

    def get_active(self) -> list[Customer]:
        return Customer.query.filter(
            Customer.is_active == True,
            Customer.is_deleted == False,
        ).all()

    def search(self, term: str) -> list[Customer]:
        pattern = f'%{term}%'
        return Customer.query.filter(
            Customer.is_deleted == False,
            (
                Customer.name.ilike(pattern) |
                Customer.customer_code.ilike(pattern) |
                Customer.phone.ilike(pattern) |
                Customer.email.ilike(pattern) |
                Customer.tin_number.ilike(pattern)
            ),
        ).all()
