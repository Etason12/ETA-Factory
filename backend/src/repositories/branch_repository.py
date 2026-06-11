from typing import Optional

from models.models import Branch
from repositories.base import BaseRepository


class BranchRepository(BaseRepository[Branch]):
    def __init__(self) -> None:
        super().__init__(Branch)

    def get_by_code(self, code: str) -> Optional[Branch]:
        return Branch.query.filter(
            Branch.code == code,
            Branch.is_deleted == False,
        ).first()

    def get_by_name(self, name: str) -> Optional[Branch]:
        return Branch.query.filter(
            Branch.name == name,
            Branch.is_deleted == False,
        ).first()

    def get_active(self) -> list[Branch]:
        return Branch.query.filter(
            Branch.is_active == True,
            Branch.is_deleted == False,
        ).all()

    def search(self, term: str) -> list[Branch]:
        pattern = f'%{term}%'
        return Branch.query.filter(
            Branch.is_deleted == False,
            (
                Branch.name.ilike(pattern) |
                Branch.code.ilike(pattern) |
                Branch.city.ilike(pattern)
            ),
        ).all()
