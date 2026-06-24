from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Optional

from sqlalchemy import func as sa_func

from models.models import (
    GIVItem,
    GRVItem,
    GoodsIssueVoucher,
    GoodsReceiveVoucher,
    Inventory,
    InventoryLedger,
    Product,
    RawMaterialInventory,
    RawMaterialLedger,
    StockAdjustment,
    StockAdjustmentItem,
    User,
    Warehouse,
    db,
)
from repositories.base import BaseRepository
from utils.error_handlers import NotFoundError, ValidationError
from utils.helpers import generate_code, paginate


def _calculate_average_cost(product_id: int, warehouse_id: int) -> float:
    result = InventoryLedger.query.with_entities(
        sa_func.sum(InventoryLedger.quantity * InventoryLedger.unit_cost),
        sa_func.sum(InventoryLedger.quantity),
    ).filter(
        InventoryLedger.product_id == product_id,
        InventoryLedger.warehouse_id == warehouse_id,
        InventoryLedger.unit_cost.isnot(None),
    ).first()

    if result and result[1] and float(result[1]) != 0:
        return float(result[0]) / float(result[1])
    return 0


def calculate_unit_cost(product: Product, warehouse_id: int) -> Optional[float]:
    method = (product.costing_method or 'standard').lower()
    if method == 'standard':
        return float(product.cost_price) if product.cost_price else None

    if method == 'weighted_average':
        avg = _calculate_average_cost(product.id, warehouse_id)
        if avg:
            return avg
        return float(product.cost_price) if product.cost_price else None

    if method == 'fifo':
        oldest = InventoryLedger.query.filter(
            InventoryLedger.product_id == product.id,
            InventoryLedger.warehouse_id == warehouse_id,
            InventoryLedger.quantity > 0,
            InventoryLedger.unit_cost.isnot(None),
        ).order_by(InventoryLedger.transaction_date.asc()).first()
        if oldest:
            return float(oldest.unit_cost)
        return float(product.cost_price) if product.cost_price else None

    return None


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self) -> None:
        super().__init__(Inventory)

    def get_by_product_and_warehouse(
        self, product_id: int, warehouse_id: int
    ) -> Optional[Inventory]:
        return Inventory.query.filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        ).first()

    def get_by_product_warehouse_and_batch(
        self, product_id: int, warehouse_id: int, batch_number: Optional[str] = None
    ) -> Optional[Inventory]:
        query = Inventory.query.filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
        if batch_number:
            query = query.filter(Inventory.batch_number == batch_number)
        else:
            query = query.filter(Inventory.batch_number.is_(None))
        return query.first()

    def get_by_warehouse(self, warehouse_id: int) -> list[Inventory]:
        return Inventory.query.filter(
            Inventory.warehouse_id == warehouse_id,
        ).all()


class StockAdjustmentRepository(BaseRepository[StockAdjustment]):
    def __init__(self) -> None:
        super().__init__(StockAdjustment)


class InventoryLedgerRepository(BaseRepository[InventoryLedger]):
    def __init__(self) -> None:
        super().__init__(InventoryLedger)


class GoodsIssueVoucherRepository(BaseRepository[GoodsIssueVoucher]):
    def __init__(self) -> None:
        super().__init__(GoodsIssueVoucher)


class GoodsReceiveVoucherRepository(BaseRepository[GoodsReceiveVoucher]):
    def __init__(self) -> None:
        super().__init__(GoodsReceiveVoucher)


class InventoryService:
    def __init__(
        self,
        inventory_repository: Optional[InventoryRepository] = None,
        ledger_repository: Optional[InventoryLedgerRepository] = None,
        adjustment_repository: Optional[StockAdjustmentRepository] = None,
        giv_repository: Optional[GoodsIssueVoucherRepository] = None,
        grv_repository: Optional[GoodsReceiveVoucherRepository] = None,
    ):
        self.inv_repo = inventory_repository or InventoryRepository()
        self.ledger_repo = ledger_repository or InventoryLedgerRepository()
        self.adjustment_repo = adjustment_repository or StockAdjustmentRepository()
        self.giv_repo = giv_repository or GoodsIssueVoucherRepository()
        self.grv_repo = grv_repository or GoodsReceiveVoucherRepository()

    def get_stock_level(
        self, product_id: int, warehouse_id: Optional[int] = None
    ) -> dict[str, Any]:
        query = Inventory.query.filter(Inventory.product_id == product_id)
        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)

        records = query.all()
        if not records:
            return {
                'product_id': product_id,
                'total_quantity': 0,
                'total_available': 0,
                'warehouses': [],
            }

        total_quantity = sum(float(r.quantity_on_hand or 0) for r in records)
        total_reserved = sum(float(r.reserved_quantity or 0) for r in records)

        return {
            'product_id': product_id,
            'total_quantity': total_quantity,
            'total_reserved': total_reserved,
            'total_available': total_quantity - total_reserved,
            'warehouses': [
                {
                    'warehouse_id': r.warehouse_id,
                    'warehouse_name': r.warehouse.name if r.warehouse else None,
                    'quantity_on_hand': float(r.quantity_on_hand or 0),
                    'reserved_quantity': float(r.reserved_quantity or 0),
                    'available_quantity': float(r.available_quantity),
                    'batch_number': r.batch_number,
                }
                for r in records
            ],
        }

    def get_available(
        self, product_id: int, warehouse_id: int
    ) -> dict[str, Any]:
        records = Inventory.query.filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        ).all()
        if not records:
            return {
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'quantity_on_hand': 0,
                'reserved_quantity': 0,
                'available_quantity': 0,
            }

        total_qty = sum(float(r.quantity_on_hand or 0) for r in records)
        total_reserved = sum(float(r.reserved_quantity or 0) for r in records)
        return {
            'product_id': product_id,
            'warehouse_id': warehouse_id,
            'quantity_on_hand': total_qty,
            'reserved_quantity': total_reserved,
            'available_quantity': total_qty - total_reserved,
        }

    def _get_or_create_inventory(
        self, product_id: int, warehouse_id: int, batch_number: Optional[str] = None,
        lock: bool = False
    ) -> Inventory:
        batch = batch_number if batch_number else None
        if batch is not None:
            query = Inventory.query.filter(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
                Inventory.batch_number == batch
            )
            if lock:
                query = query.with_for_update()
            inv = query.first()
            if not inv:
                inv = Inventory(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity_on_hand=0,
                    reserved_quantity=0,
                    batch_number=batch,
                )
                inv = self.inv_repo.create(inv)
            return inv

        query = Inventory.query.filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
            Inventory.batch_number.is_(None)
        )
        if lock:
            query = query.with_for_update()
        
        inv = query.order_by(Inventory.quantity_on_hand.desc()).first()
        if inv:
            return inv
        
        inv = Inventory(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=0,
            reserved_quantity=0,
            batch_number=None,
        )
        inv = self.inv_repo.create(inv)
        return inv

    def _create_ledger_entry(
        self,
        product_id: int,
        warehouse_id: int,
        movement_type: str,
        quantity: float,
        unit_cost: Optional[float] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        batch_number: Optional[str] = None,
        created_by_id: Optional[int] = None,
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
            created_by_id=created_by_id,
        )
        return self.ledger_repo.create(entry)

    def _calculate_average_cost(self, product_id: int, warehouse_id: int) -> float:
        return _calculate_average_cost(product_id, warehouse_id)

    def get_unit_cost(
        self, product: Product, warehouse_id: int
    ) -> Optional[float]:
        return calculate_unit_cost(product, warehouse_id)

    def _check_permission(self, permission_name: str, user_id: Optional[int]):
        if user_id is None:
            return
        
        user = User.query.get(user_id)
        if not user or not user.role:
            raise ValidationError('No role assigned to user')
        
        has_perm = any(p.name == permission_name for p in user.role.permissions)
        if not has_perm:
            raise ValidationError(f'Missing permission: {permission_name}')

    def adjust_stock(
        self,
        product_id: int,
        warehouse_id: int,
        adjustment_type: str,
        quantity: float,
        reason: str,
        unit_cost: Optional[float] = None,
        batch_number: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> dict[str, Any]:
        self._check_permission('inventory.adjust', created_by_id)
        if quantity <= 0:
            raise ValidationError('Quantity must be positive')


        try:
            inv = self._get_or_create_inventory(product_id, warehouse_id, batch_number, lock=True)
            current_qty = float(inv.quantity_on_hand or 0)

            if adjustment_type == 'Addition':
                new_qty = current_qty + quantity
            elif adjustment_type == 'Reduction':
                if current_qty < quantity:
                    raise ValidationError(
                        f'Insufficient stock. Available: {current_qty}, Requested reduction: {quantity}'
                    )
                new_qty = current_qty - quantity
            else:
                raise ValidationError(f'Invalid adjustment type: {adjustment_type}')

            cost = unit_cost if unit_cost else self._calculate_average_cost(product_id, warehouse_id)

            inv.quantity_on_hand = new_qty
            self.inv_repo.update(inv)

            self._create_ledger_entry(
                product_id=product_id,
                warehouse_id=warehouse_id,
                movement_type=adjustment_type,
                quantity=quantity if adjustment_type == 'Addition' else -quantity,
                unit_cost=cost,
                reference_type='Adjustment',
                batch_number=batch_number,
                created_by_id=created_by_id,
            )
            db.session.commit()

            return {
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'previous_quantity': current_qty,
                'new_quantity': new_qty,
                'adjustment_type': adjustment_type,
                'adjustment_quantity': quantity,
            }
        except Exception:
            db.session.rollback()
            raise

    def reserve_stock(
        self, product_id: int, warehouse_id: int, quantity: float
    ) -> None:
        inv = self._get_or_create_inventory(product_id, warehouse_id)
        available = float(inv.available_quantity)

        if available < quantity:
            raise ValidationError(
                f'Insufficient available stock. Available: {available}, Requested: {quantity}'
            )

        inv.reserved_quantity = float(inv.reserved_quantity or 0) + quantity
        self.inv_repo.update(inv)

    def release_stock(
        self, product_id: int, warehouse_id: int, quantity: float
    ) -> None:
        inv = self._get_or_create_inventory(product_id, warehouse_id)
        reserved = float(inv.reserved_quantity or 0)

        if reserved < quantity:
            inv.reserved_quantity = 0
        else:
            inv.reserved_quantity = reserved - quantity

        self.inv_repo.update(inv)

    def set_opening_balance(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: float,
        batch_number: Optional[str] = None,
        unit_cost: Optional[float] = None,
        created_by_id: Optional[int] = None,
    ) -> Inventory:
        self._check_permission('inventory.adjust', created_by_id)
        existing = InventoryLedger.query.filter_by(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type='Opening Balance',
        ).first()

        if existing:
            raise ValidationError(f'Opening balance already exists for this product in warehouse {warehouse_id}')

        inv = self._get_or_create_inventory(product_id, warehouse_id, batch_number)
        inv.quantity_on_hand = quantity
        inv.reserved_quantity = 0
        self.inv_repo.update(inv)

        self._create_ledger_entry(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type='Opening Balance',
            quantity=quantity,
            unit_cost=unit_cost,
            batch_number=batch_number,
            created_by_id=created_by_id,
        )

        return inv

    def set_raw_material_opening_balance(
        self,
        raw_material_id: int,
        warehouse_id: int,
        quantity: float,
        unit_cost: Optional[float] = None,
        created_by_id: Optional[int] = None,
    ) -> RawMaterialInventory:
        self._check_permission('inventory.adjust', created_by_id)
        existing = RawMaterialLedger.query.filter_by(
            raw_material_id=raw_material_id,
            warehouse_id=warehouse_id,
            movement_type='Opening Balance',
        ).first()

        if existing:
            raise ValidationError(f'Opening balance already exists for this raw material in warehouse {warehouse_id}')

        inv = RawMaterialInventory.query.filter_by(
            raw_material_id=raw_material_id,
            warehouse_id=warehouse_id,
        ).first()
        if not inv:
            inv = RawMaterialInventory(
                raw_material_id=raw_material_id,
                warehouse_id=warehouse_id,
                quantity_on_hand=quantity,
                reserved_quantity=0,
            )
            db.session.add(inv)
        else:
            inv.quantity_on_hand = quantity
            inv.reserved_quantity = 0

        db.session.flush()

        ledger = RawMaterialLedger(
            raw_material_id=raw_material_id,
            warehouse_id=warehouse_id,
            movement_type='Opening Balance',
            quantity=quantity,
            unit_cost=unit_cost,
            created_by_id=created_by_id,
        )
        db.session.add(ledger)

        return inv

    def deduct_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: float,
        unit_cost: Optional[float] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        batch_number: Optional[str] = None,
        created_by_id: Optional[int] = None,
        sales_order_item_id: Optional[int] = None,
    ) -> None:
        batch = batch_number if batch_number else None
        inv = self._get_or_create_inventory(product_id, warehouse_id, batch, lock=True)
        current_qty = float(inv.quantity_on_hand or 0)

        if current_qty < quantity:
            raise ValidationError(
                f'Insufficient stock. On hand: {current_qty}, Requested: {quantity}'
            )

        reserved = float(inv.reserved_quantity or 0)
        new_reserved = max(0, reserved - quantity)

        cost = unit_cost if unit_cost else self._calculate_average_cost(product_id, warehouse_id)

        # Update COGS in SalesOrderItem if requested
        if sales_order_item_id:
            from models.models import SalesOrderItem, db
            soi = SalesOrderItem.query.get(sales_order_item_id)
            if soi:
                soi.cost_price = cost
                db.session.add(soi)

        inv.quantity_on_hand = current_qty - quantity
        inv.reserved_quantity = new_reserved
        self.inv_repo.update(inv)

        self._create_ledger_entry(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type='Issue',
            quantity=-quantity,
            unit_cost=cost,
            reference_type=reference_type,
            reference_id=reference_id,
            batch_number=batch_number or inv.batch_number,
            created_by_id=created_by_id,
        )

    def add_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: float,
        unit_cost: Optional[float] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        batch_number: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> None:
        inv = self._get_or_create_inventory(product_id, warehouse_id, batch_number, lock=True)

        inv.quantity_on_hand = float(inv.quantity_on_hand or 0) + quantity
        self.inv_repo.update(inv)

        self._create_ledger_entry(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type='Receipt',
            quantity=quantity,
            unit_cost=unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            batch_number=batch_number,
            created_by_id=created_by_id,
        )

    def create_goods_issue_voucher(
        self,
        warehouse_id: int,
        items: list[dict[str, Any]],
        sales_order_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        notes: Optional[str] = None,
        created_by_id: Optional[int] = None,
        issued_by_id: Optional[int] = None,
    ) -> GoodsIssueVoucher:
        from datetime import date

        today = date.today()
        count = GoodsIssueVoucher.query.filter(
            GoodsIssueVoucher.voucher_date == today
        ).count() + 1
        voucher_number = f'GIV-{today.strftime("%Y%m%d")}-{count:05d}'

        giv = GoodsIssueVoucher(
            voucher_number=voucher_number,
            warehouse_id=warehouse_id,
            sales_order_id=sales_order_id,
            voucher_date=today,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            status='Draft',
            created_by_id=created_by_id,
            issued_by_id=issued_by_id,
        )
        giv = self.giv_repo.create(giv)

        for item_data in items:
            giv_item = GIVItem(
                giv_id=giv.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                batch_number=item_data.get('batch_number'),
            )
            db.session.add(giv_item)

        return giv

    def create_goods_receive_voucher(
        self,
        warehouse_id: int,
        items: list[dict[str, Any]],
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        notes: Optional[str] = None,
        created_by_id: Optional[int] = None,
        received_by_id: Optional[int] = None,
    ) -> GoodsReceiveVoucher:
        from datetime import date

        today = date.today()
        count = GoodsReceiveVoucher.query.filter(
            GoodsReceiveVoucher.voucher_date == today
        ).count() + 1
        voucher_number = f'GRV-{today.strftime("%Y%m%d")}-{count:05d}'

        grv = GoodsReceiveVoucher(
            voucher_number=voucher_number,
            warehouse_id=warehouse_id,
            voucher_date=today,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            status='Draft',
            created_by_id=created_by_id,
            received_by_id=received_by_id,
        )
        grv = self.grv_repo.create(grv)

        for item_data in items:
            grv_item = GRVItem(
                grv_id=grv.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_cost=item_data.get('unit_cost'),
                batch_number=item_data.get('batch_number'),
            )
            db.session.add(grv_item)

        return grv

    def process_goods_issue(
        self,
        giv_id: int,
        issued_by_id: Optional[int] = None,
        commit: bool = True,
    ) -> GoodsIssueVoucher:
        try:
            giv = self.giv_repo.get_by_id(giv_id)
            if not giv:
                raise NotFoundError('Goods Issue Voucher not found')

            if giv.status == 'Issued':
                raise ValidationError('Goods already issued')

            for item in giv.items:
                unit_cost = self.get_unit_cost(item.product, giv.warehouse_id) if item.product else None
                # Assuming item corresponds to a SalesOrderItem when GIV is linked to a SalesOrder
                sales_order_item_id = None
                if giv.sales_order_id:
                    from models.models import SalesOrderItem
                    soi = SalesOrderItem.query.filter_by(
                        sales_order_id=giv.sales_order_id,
                        product_id=item.product_id
                    ).first()
                    if soi:
                        sales_order_item_id = soi.id

                self.deduct_stock(
                    product_id=item.product_id,
                    warehouse_id=giv.warehouse_id,
                    quantity=float(item.quantity),
                    unit_cost=unit_cost,
                    reference_type=giv.reference_type or 'GIV',
                    reference_id=giv.id,
                    batch_number=item.batch_number,
                    created_by_id=issued_by_id,
                    sales_order_item_id=sales_order_item_id
                )

            giv.status = 'Issued'
            giv.issued_by_id = issued_by_id
            self.giv_repo.update(giv)
            if commit:
                db.session.commit()

            return giv
        except Exception:
            db.session.rollback()
            raise

    def reverse_goods_issue(
        self,
        sales_order_id: int,
        cancelled_by_id: int,
    ) -> GoodsIssueVoucher:
        giv = GoodsIssueVoucher.query.filter_by(
            sales_order_id=sales_order_id,
            status='Issued',
        ).first()
        if not giv:
            raise NotFoundError('No issued GIV found for this sales order')

        for item in giv.items:
            unit_cost = self.get_unit_cost(item.product, giv.warehouse_id) if item.product else None
            self.add_stock(
                product_id=item.product_id,
                warehouse_id=giv.warehouse_id,
                quantity=float(item.quantity),
                unit_cost=unit_cost,
                reference_type='Return',
                reference_id=giv.id,
                batch_number=item.batch_number,
                created_by_id=cancelled_by_id,
            )

        giv.status = 'Cancelled'
        self.giv_repo.update(giv)

        return giv

    def process_goods_receipt(
        self,
        grv_id: int,
        received_by_id: Optional[int] = None,
        commit: bool = True,
    ) -> GoodsReceiveVoucher:
        try:
            grv = self.grv_repo.get_by_id(grv_id)
            if not grv:
                raise NotFoundError('Goods Receive Voucher not found')

            if grv.status == 'Received':
                raise ValidationError('Goods already received')

            for item in grv.items:
                self.add_stock(
                    product_id=item.product_id,
                    warehouse_id=grv.warehouse_id,
                    quantity=float(item.quantity),
                    unit_cost=float(item.unit_cost) if item.unit_cost else None,
                    reference_type=grv.reference_type or 'GRV',
                    reference_id=grv.id,
                    batch_number=item.batch_number,
                    created_by_id=received_by_id,
                )

            grv.status = 'Received'
            grv.received_by_id = received_by_id
            self.grv_repo.update(grv)
            if commit:
                db.session.commit()

            return grv
        except Exception:
            db.session.rollback()
            raise
