from typing import Any, Optional

import bcrypt

from models.models import User
from repositories.user_repository import UserRepository
from repositories.branch_repository import BranchRepository
from utils.error_handlers import ConflictError, NotFoundError, ValidationError


class UserService:
    def __init__(
        self,
        user_repository: Optional[UserRepository] = None,
        branch_repository: Optional[BranchRepository] = None,
    ):
        self.user_repo = user_repository or UserRepository()
        self.branch_repo = branch_repository or BranchRepository()

    def get_user(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError('User not found')
        return user

    def get_users(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        return self.user_repo.get_all(
            page=page, per_page=per_page, filters=filters, sort=sort, order=order
        )

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role_id: int,
        branch_id: Optional[int] = None,
        phone: Optional[str] = None,
    ) -> User:
        if self.user_repo.get_by_username(username):
            raise ConflictError(f'Username "{username}" already exists')

        if self.user_repo.get_by_email(email):
            raise ConflictError(f'Email "{email}" already exists')

        if len(password) < 6:
            raise ValidationError('Password must be at least 6 characters')

        if branch_id:
            branch = self.branch_repo.get_by_id(branch_id)
            if not branch:
                raise ValidationError('Branch not found')

        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            role_id=role_id,
            branch_id=branch_id,
            is_active=True,
        )
        return self.user_repo.create(user)

    def update_user(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        user = self.get_user(user_id)

        if email is not None and email != user.email:
            existing = self.user_repo.get_by_email(email)
            if existing and existing.id != user_id:
                raise ConflictError(f'Email "{email}" already in use')
            user.email = email

        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        if role_id is not None:
            user.role_id = role_id
        if branch_id is not None:
            if branch_id:
                branch = self.branch_repo.get_by_id(branch_id)
                if not branch:
                    raise ValidationError('Branch not found')
            user.branch_id = branch_id
        if is_active is not None:
            user.is_active = is_active

        return self.user_repo.update(user)

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        self.user_repo.delete(user)

    def assign_role(self, user_id: int, role_id: int) -> User:
        user = self.get_user(user_id)
        user.role_id = role_id
        return self.user_repo.update(user)
