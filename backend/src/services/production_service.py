from datetime import date, datetime
from typing import Any, Optional

from models.models import ProductionBatch
from repositories.base import BaseRepository
from services.inventory_service import InventoryService
from utils.error_handlers import NotFoundError, ValidationError


class ProductionBatchRepository(BaseRepository[ProductionBatch]):
    def __init__(self) -> None:
        super().__init__(ProductionBatch)

    def get_by_batch_number(self, batch_number: str) -> Optional[ProductionBatch]:
        return ProductionBatch.query.filter(
            ProductionBatch.batch_number == batch_number
        ).first()


class ProductionService:
    def __init__(
        self,
        production_repository: Optional[ProductionBatchRepository] = None,
        inventory_service: Optional[InventoryService] = None,
    ):
        self.repo = production_repository or ProductionBatchRepository()
        self.inventory_service = inventory_service or InventoryService()

    def get_batch(self, batch_id: int) -> ProductionBatch:
        batch = self.repo.get_by_id(batch_id)
        if not batch:
            raise NotFoundError('Production batch not found')
        return batch

    def get_batches(
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

    def _generate_batch_number(self) -> str:
        today = date.today()
        count = ProductionBatch.query.filter(
            ProductionBatch.production_date == today
        ).count() + 1
        return f'PRD-{today.strftime("%Y%m%d")}-{count:05d}'

    def create_batch(
        self,
        product_id: int,
        quantity_produced: float,
        production_cost: float,
        production_date: date,
        warehouse_id: int,
        notes: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> ProductionBatch:
        if quantity_produced <= 0:
            raise ValidationError('Quantity produced must be positive')
        if not product_id:
            raise ValidationError('Product is required')
        if not warehouse_id:
            raise ValidationError('Warehouse is required')
        if not production_date:
            raise ValidationError('Production date is required')

        from models.models import Product, Warehouse

        product = Product.query.get(product_id)
        if not product:
            raise ValidationError('Product not found')

        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            raise ValidationError('Warehouse not found')

        batch_number = self._generate_batch_number()

        batch = ProductionBatch(
            batch_number=batch_number,
            product_id=product_id,
            quantity_produced=quantity_produced,
            production_cost=production_cost,
            production_date=production_date,
            warehouse_id=warehouse_id,
            notes=notes,
            status='Pending',
        )

        return self.repo.create(batch)

    def approve_batch(
        self,
        batch_id: int,
        approved_by_id: int,
    ) -> ProductionBatch:
        batch = self.get_batch(batch_id)

        if batch.status != 'Pending':
            raise ValidationError(f'Batch is already {batch.status}')

        batch.status = 'Approved'
        batch.approved_by_id = approved_by_id
        batch.approved_at = datetime.utcnow()
        self.repo.update(batch)

        unit_cost = (
            float(batch.production_cost) / float(batch.quantity_produced)
            if float(batch.quantity_produced) > 0
            else 0
        )

        grv = self.inventory_service.create_goods_receive_voucher(
            warehouse_id=batch.warehouse_id,
            items=[
                {
                    'product_id': batch.product_id,
                    'quantity': float(batch.quantity_produced),
                    'unit_cost': unit_cost,
                    'batch_number': batch.batch_number,
                }
            ],
            reference_type='ProductionBatch',
            reference_id=batch.id,
            notes=f'Auto-generated GRV for production batch {batch.batch_number}',
            created_by_id=approved_by_id,
            received_by_id=approved_by_id,
        )

        self.inventory_service.process_goods_receipt(grv.id, approved_by_id)

        return batch
