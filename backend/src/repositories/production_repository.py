from datetime import date
from typing import Optional

from models.models import ProductionBatch
from repositories.base import BaseRepository


class ProductionBatchRepository(BaseRepository[ProductionBatch]):
    def __init__(self) -> None:
        super().__init__(ProductionBatch)

    def get_by_batch_number(self, batch_number: str) -> Optional[ProductionBatch]:
        return ProductionBatch.query.filter_by(batch_number=batch_number).first()

    def get_by_product(self, product_id: int) -> list[ProductionBatch]:
        return ProductionBatch.query.filter_by(product_id=product_id).order_by(
            ProductionBatch.production_date.desc(),
        ).all()

    def get_by_status(self, status: str) -> list[ProductionBatch]:
        return ProductionBatch.query.filter_by(status=status).all()

    def get_by_warehouse(self, warehouse_id: int) -> list[ProductionBatch]:
        return ProductionBatch.query.filter_by(warehouse_id=warehouse_id).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[ProductionBatch]:
        return ProductionBatch.query.filter(
            ProductionBatch.production_date.between(start_date, end_date),
        ).all()

    def get_pending(self) -> list[ProductionBatch]:
        return ProductionBatch.query.filter(
            ProductionBatch.status.in_(['Pending', 'In Progress']),
        ).all()

    def get_completed(self) -> list[ProductionBatch]:
        return ProductionBatch.query.filter_by(status='Completed').all()
