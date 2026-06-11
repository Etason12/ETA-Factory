from decimal import Decimal
from typing import Any, Optional

from models.models import Inventory, InventoryLedger, db
from repositories.base import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self) -> None:
        super().__init__(Inventory)

    def get_by_product_warehouse(
        self, product_id: int, warehouse_id: int, batch_number: Optional[str] = None,
    ) -> Optional[Inventory]:
        query = Inventory.query.filter_by(
            product_id=product_id,
            warehouse_id=warehouse_id,
        )
        if batch_number is not None:
            query = query.filter_by(batch_number=batch_number)
        else:
            query = query.filter(Inventory.batch_number.is_(None))
        return query.first()

    def get_or_create(
        self, product_id: int, warehouse_id: int, batch_number: Optional[str] = None,
    ) -> Inventory:
        inventory = self.get_by_product_warehouse(product_id, warehouse_id, batch_number)
        if inventory:
            return inventory
        inventory = Inventory(
            product_id=product_id,
            warehouse_id=warehouse_id,
            batch_number=batch_number,
            quantity_on_hand=Decimal('0'),
            reserved_quantity=Decimal('0'),
        )
        return self.create(inventory)

    def get_available_quantity(
        self, product_id: int, warehouse_id: int, batch_number: Optional[str] = None,
    ) -> Decimal:
        inventory = self.get_by_product_warehouse(product_id, warehouse_id, batch_number)
        if not inventory:
            return Decimal('0')
        return Decimal(str(inventory.available_quantity))

    def update_quantity_on_hand(
        self, product_id: int, warehouse_id: int, delta: Decimal,
        batch_number: Optional[str] = None,
    ) -> Inventory:
        inventory = self.get_or_create(product_id, warehouse_id, batch_number)
        inventory.quantity_on_hand = Decimal(str(inventory.quantity_on_hand or 0)) + delta
        db.session.commit()
        return inventory

    def reserve_quantity(
        self, product_id: int, warehouse_id: int, quantity: Decimal,
        batch_number: Optional[str] = None,
    ) -> Inventory:
        inventory = self.get_or_create(product_id, warehouse_id, batch_number)
        inventory.reserved_quantity = Decimal(str(inventory.reserved_quantity or 0)) + quantity
        db.session.commit()
        return inventory

    def release_reserved(
        self, product_id: int, warehouse_id: int, quantity: Decimal,
        batch_number: Optional[str] = None,
    ) -> Inventory:
        inventory = self.get_or_create(product_id, warehouse_id, batch_number)
        inventory.reserved_quantity = max(
            Decimal('0'),
            Decimal(str(inventory.reserved_quantity or 0)) - quantity,
        )
        db.session.commit()
        return inventory

    def create_ledger_entry(
        self,
        product_id: int,
        warehouse_id: int,
        movement_type: str,
        quantity: Decimal,
        unit_cost: Optional[Decimal] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        batch_number: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> InventoryLedger:
        entry = InventoryLedger(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            batch_number=batch_number,
            created_by_id=user_id,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def get_ledger_entries(
        self,
        product_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        movement_type: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[InventoryLedger]:
        query = InventoryLedger.query
        if product_id is not None:
            query = query.filter_by(product_id=product_id)
        if warehouse_id is not None:
            query = query.filter_by(warehouse_id=warehouse_id)
        if movement_type is not None:
            query = query.filter_by(movement_type=movement_type)
        if reference_type is not None:
            query = query.filter_by(reference_type=reference_type)
        if reference_id is not None:
            query = query.filter_by(reference_id=reference_id)
        return query.order_by(InventoryLedger.transaction_date.desc()).limit(limit).all()

    def get_inventory_by_warehouse(self, warehouse_id: int) -> list[Inventory]:
        return Inventory.query.filter_by(warehouse_id=warehouse_id).all()

    def get_inventory_by_product(self, product_id: int) -> list[Inventory]:
        return Inventory.query.filter_by(product_id=product_id).all()

    def get_low_stock_items(self, threshold: Decimal = Decimal('10')) -> list[Inventory]:
        return Inventory.query.filter(
            Inventory.quantity_on_hand <= threshold,
        ).all()

    def get_stock_value(self, warehouse_id: Optional[int] = None) -> Decimal:
        query = Inventory.query
        if warehouse_id is not None:
            query = query.filter_by(warehouse_id=warehouse_id)
        inventories = query.all()
        total = Decimal('0')
        from models.models import Product
        for inv in inventories:
            product = Product.query.get(inv.product_id)
            if product and product.cost_price:
                total += Decimal(str(inv.quantity_on_hand or 0)) * Decimal(str(product.cost_price))
        return total
