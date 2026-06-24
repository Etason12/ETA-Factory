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

    def get_required_materials(
        self, product_id: int, quantity: float, warehouse_id: int
    ) -> list[dict[str, Any]]:
        from models.models import Product, BOMItem, RawMaterial, RawMaterialInventory, db
        
        product = Product.query.get(product_id)
        if not product:
            raise NotFoundError('Product not found')

        bom_items = BOMItem.query.filter_by(product_id=product_id).all()
        requirements = []
        
        for item in bom_items:
            required_qty = float(item.quantity) * quantity
            rm = item.raw_material

            inv = RawMaterialInventory.query.filter(
                RawMaterialInventory.raw_material_id == item.raw_material_id,
                RawMaterialInventory.warehouse_id == warehouse_id
            ).first()
            available = inv.available_quantity if inv else 0
            
            requirements.append({
                'raw_material_id': item.raw_material_id,
                'raw_material_name': rm.name,
                'raw_material_sku': rm.sku,
                'required_quantity': required_qty,
                'available_quantity': available,
                'has_enough': available >= required_qty,
                'unit_name': rm.unit.name if rm.unit else None,
                'unit_cost': float(rm.cost_price or 0),
            })
            
        return requirements

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

        from models.models import Product, Warehouse, BOMItem

        product = Product.query.get(product_id)
        if not product:
            raise ValidationError('Product not found')

        # Check if product has BOM defined
        bom_count = BOMItem.query.filter_by(product_id=product_id).count()
        if bom_count == 0:
            raise ValidationError(f'Product {product.name} has no Bill of Materials (BOM) defined. Please create a BOM first.')

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
        from models.models import db, BOMItem, RawMaterial, RawMaterialInventory, RawMaterialLedger
        batch = self.get_batch(batch_id)

        if batch.status != 'Pending':
            raise ValidationError(f'Batch is already {batch.status}')
        
        if batch.production_cost <= 0:
            raise ValidationError('Production cost must be positive')

        try:
            # Deduct raw material stock from warehouse-level inventory
            bom_items = BOMItem.query.filter_by(product_id=batch.product_id).all()
            for item in bom_items:
                rm = item.raw_material
                needed = float(item.quantity) * float(batch.quantity_produced)

                inv = RawMaterialInventory.query.filter(
                    RawMaterialInventory.raw_material_id == item.raw_material_id,
                    RawMaterialInventory.warehouse_id == batch.warehouse_id
                ).with_for_update().first()
                available = inv.available_quantity if inv else 0

                if available < needed:
                    raise ValidationError(
                        f'Insufficient stock of {rm.name} in warehouse: need {needed}, available {available}'
                    )

                inv.quantity_on_hand = float(inv.quantity_on_hand or 0) - needed

                ledger = RawMaterialLedger(
                    raw_material_id=item.raw_material_id,
                    warehouse_id=batch.warehouse_id,
                    movement_type='ProductionIssue',
                    quantity=-needed,
                    unit_cost=float(rm.cost_price or 0),
                    reference_type='ProductionBatch',
                    reference_id=batch.id,
                    created_by_id=approved_by_id,
                )
                db.session.add(ledger)

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

            product = batch.product
            product.cost_price = unit_cost
            db.session.add(product)

            db.session.commit()
            return batch
        except Exception:
            db.session.rollback()
            raise
