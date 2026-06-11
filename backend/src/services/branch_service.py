from typing import Any, Optional

from models.models import Branch
from repositories.branch_repository import BranchRepository
from utils.error_handlers import ConflictError, NotFoundError, ValidationError


class BranchService:
    def __init__(self, branch_repository: Optional[BranchRepository] = None):
        self.repo = branch_repository or BranchRepository()

    def get_branch(self, branch_id: int) -> Branch:
        branch = self.repo.get_by_id(branch_id)
        if not branch:
            raise NotFoundError('Branch not found')
        return branch

    def get_branches(
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

    def create_branch(
        self,
        name: str,
        code: str,
        city: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Branch:
        if not name or not name.strip():
            raise ValidationError('Branch name is required')
        if not code or not code.strip():
            raise ValidationError('Branch code is required')

        if self.repo.get_by_code(code):
            raise ConflictError(f'Branch code "{code}" already exists')
        if self.repo.get_by_name(name):
            raise ConflictError(f'Branch name "{name}" already exists')

        branch = Branch(
            name=name.strip(),
            code=code.strip().upper(),
            city=city,
            address=address,
            phone=phone,
            email=email,
            is_active=True,
        )
        return self.repo.create(branch)

    def update_branch(
        self,
        branch_id: int,
        name: Optional[str] = None,
        code: Optional[str] = None,
        city: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Branch:
        branch = self.get_branch(branch_id)

        if name is not None:
            if not name.strip():
                raise ValidationError('Branch name cannot be empty')
            existing = self.repo.get_by_name(name)
            if existing and existing.id != branch_id:
                raise ConflictError(f'Branch name "{name}" already exists')
            branch.name = name.strip()

        if code is not None:
            if not code.strip():
                raise ValidationError('Branch code cannot be empty')
            code_upper = code.strip().upper()
            existing = self.repo.get_by_code(code_upper)
            if existing and existing.id != branch_id:
                raise ConflictError(f'Branch code "{code}" already exists')
            branch.code = code_upper

        if city is not None:
            branch.city = city
        if address is not None:
            branch.address = address
        if phone is not None:
            branch.phone = phone
        if email is not None:
            branch.email = email
        if is_active is not None:
            branch.is_active = is_active

        return self.repo.update(branch)

    def delete_branch(self, branch_id: int) -> None:
        branch = self.get_branch(branch_id)
        self.repo.delete(branch)
