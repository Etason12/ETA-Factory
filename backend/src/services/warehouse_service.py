from typing import Any, Optional

from models.models import Warehouse
from repositories.base import BaseRepository
from repositories.branch_repository import BranchRepository
from utils.error_handlers import ConflictError, NotFoundError, ValidationError


class WarehouseRepository(BaseRepository[Warehouse]):
    def __init__(self) -> None:
        super().__init__(Warehouse)

    def get_by_code(self, code: str) -> Optional[Warehouse]:
        return Warehouse.query.filter(
            Warehouse.code == code,
            Warehouse.is_deleted == False,
        ).first()

    def get_by_branch(self, branch_id: int) -> list[Warehouse]:
        return Warehouse.query.filter(
            Warehouse.branch_id == branch_id,
            Warehouse.is_deleted == False,
        ).all()

    def get_active(self) -> list[Warehouse]:
        return Warehouse.query.filter(
            Warehouse.is_active == True,
            Warehouse.is_deleted == False,
        ).all()


class WarehouseService:
    def __init__(
        self,
        warehouse_repository: Optional[WarehouseRepository] = None,
        branch_repository: Optional[BranchRepository] = None,
    ):
        self.repo = warehouse_repository or WarehouseRepository()
        self.branch_repo = branch_repository or BranchRepository()

    def get_warehouse(self, warehouse_id: int) -> Warehouse:
        warehouse = self.repo.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError('Warehouse not found')
        return warehouse

    def get_warehouses(
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

    def get_warehouses_by_branch(self, branch_id: int) -> list[Warehouse]:
        branch = self.branch_repo.get_by_id(branch_id)
        if not branch:
            raise NotFoundError('Branch not found')
        return self.repo.get_by_branch(branch_id)

    def create_warehouse(
        self,
        name: str,
        code: str,
        type: str,
        branch_id: int,
        address: Optional[str] = None,
    ) -> Warehouse:
        if not name or not name.strip():
            raise ValidationError('Warehouse name is required')
        if not code or not code.strip():
            raise ValidationError('Warehouse code is required')
        if not type or not type.strip():
            raise ValidationError('Warehouse type is required')

        if self.repo.get_by_code(code):
            raise ConflictError(f'Warehouse code "{code}" already exists')

        branch = self.branch_repo.get_by_id(branch_id)
        if not branch:
            raise ValidationError('Branch not found')

        warehouse = Warehouse(
            name=name.strip(),
            code=code.strip().upper(),
            type=type,
            address=address,
            branch_id=branch_id,
            is_active=True,
        )
        return self.repo.create(warehouse)

    def update_warehouse(
        self,
        warehouse_id: int,
        name: Optional[str] = None,
        code: Optional[str] = None,
        type: Optional[str] = None,
        address: Optional[str] = None,
        branch_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Warehouse:
        warehouse = self.get_warehouse(warehouse_id)

        if name is not None:
            if not name.strip():
                raise ValidationError('Warehouse name cannot be empty')
            warehouse.name = name.strip()
        if code is not None:
            if not code.strip():
                raise ValidationError('Warehouse code cannot be empty')
            code_upper = code.strip().upper()
            existing = self.repo.get_by_code(code_upper)
            if existing and existing.id != warehouse_id:
                raise ConflictError(f'Warehouse code "{code}" already exists')
            warehouse.code = code_upper
        if type is not None:
            warehouse.type = type
        if address is not None:
            warehouse.address = address
        if branch_id is not None:
            branch = self.branch_repo.get_by_id(branch_id)
            if not branch:
                raise ValidationError('Branch not found')
            warehouse.branch_id = branch_id
        if is_active is not None:
            warehouse.is_active = is_active

        return self.repo.update(warehouse)

    def delete_warehouse(self, warehouse_id: int) -> None:
        warehouse = self.get_warehouse(warehouse_id)
        self.repo.delete(warehouse)
