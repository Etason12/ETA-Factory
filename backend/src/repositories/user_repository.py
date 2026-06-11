from typing import Any, Optional

from models.models import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    def get_by_username(self, username: str) -> Optional[User]:
        return User.query.filter(
            User.username == username,
            User.is_deleted == False,
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return User.query.filter(
            User.email == email,
            User.is_deleted == False,
        ).first()

    def get_by_role(self, role_id: int) -> list[User]:
        return User.query.filter(
            User.role_id == role_id,
            User.is_deleted == False,
        ).all()

    def get_active(self) -> list[User]:
        return User.query.filter(
            User.is_active == True,
            User.is_deleted == False,
        ).all()

    def get_by_branch(self, branch_id: int) -> list[User]:
        return User.query.filter(
            User.branch_id == branch_id,
            User.is_deleted == False,
        ).all()

    def search(self, term: str) -> list[User]:
        pattern = f'%{term}%'
        return User.query.filter(
            User.is_deleted == False,
            (
                User.username.ilike(pattern) |
                User.email.ilike(pattern) |
                User.full_name.ilike(pattern) |
                User.phone.ilike(pattern)
            ),
        ).all()
