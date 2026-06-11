from datetime import date, datetime
from typing import Any, Optional

from models.models import Transfer, TransferItem
from repositories.base import BaseRepository
from services.inventory_service import InventoryService
from utils.error_handlers import NotFoundError, ValidationError


class TransferRepository(BaseRepository[Transfer]):
    def __init__(self) -> None:
        super().__init__(Transfer)

    def get_by_transfer_number(self, transfer_number: str) -> Optional[Transfer]:
        return Transfer.query.filter(
            Transfer.transfer_number == transfer_number
        ).first()


class TransferService:
    def __init__(
        self,
        transfer_repository: Optional[TransferRepository] = None,
        inventory_service: Optional[InventoryService] = None,
    ):
        self.repo = transfer_repository or TransferRepository()
        self.inventory_service = inventory_service or InventoryService()

    def get_transfer(self, transfer_id: int) -> Transfer:
        transfer = self.repo.get_by_id(transfer_id)
        if not transfer:
            raise NotFoundError('Transfer not found')
        return transfer

    def get_transfers(
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

    def _generate_transfer_number(self) -> str:
        today = date.today()
        count = Transfer.query.filter(
            Transfer.transfer_date == today
        ).count() + 1
        return f'TRF-{today.strftime("%Y%m%d")}-{count:05d}'

    def create_transfer_request(
        self,
        source_warehouse_id: int,
        destination_warehouse_id: int,
        items: list[dict[str, Any]],
        transfer_date: Optional[date] = None,
        notes: Optional[str] = None,
        requested_by_id: Optional[int] = None,
    ) -> Transfer:
        if source_warehouse_id == destination_warehouse_id:
            raise ValidationError('Source and destination warehouses must be different')

        from models.models import Warehouse

        source = Warehouse.query.get(source_warehouse_id)
        if not source:
            raise ValidationError('Source warehouse not found')

        destination = Warehouse.query.get(destination_warehouse_id)
        if not destination:
            raise ValidationError('Destination warehouse not found')

        if not items:
            raise ValidationError('At least one transfer item is required')

        transfer_number = self._generate_transfer_number()

        transfer = Transfer(
            transfer_number=transfer_number,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            transfer_date=transfer_date or date.today(),
            status='Draft',
            notes=notes,
            requested_by_id=requested_by_id,
        )
        transfer = self.repo.create(transfer)

        from models.models import db

        for item_data in items:
            item = TransferItem(
                transfer_id=transfer.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_cost=item_data.get('unit_cost'),
                batch_number=item_data.get('batch_number'),
            )
            db.session.add(item)
        db.session.commit()

        return self.repo.get_by_id(transfer.id)

    def approve_transfer(
        self,
        transfer_id: int,
        approved_by_id: int,
    ) -> Transfer:
        transfer = self.get_transfer(transfer_id)

        if transfer.status != 'Draft':
            raise ValidationError(f'Transfer is already {transfer.status}')

        transfer.status = 'Approved'
        transfer.approved_by_id = approved_by_id
        transfer.approved_at = datetime.utcnow()
        return self.repo.update(transfer)

    def issue_goods(
        self,
        transfer_id: int,
        issued_by_id: Optional[int] = None,
    ) -> Transfer:
        transfer = self.get_transfer(transfer_id)

        if transfer.status not in ('Approved',):
            raise ValidationError(
                f'Transfer must be approved before issuing goods. Current status: {transfer.status}'
            )

        items_data = []
        for item in transfer.items:
            quantity = float(item.quantity)
            items_data.append({
                'product_id': item.product_id,
                'quantity': quantity,
                'unit_cost': float(item.unit_cost) if item.unit_cost else None,
                'batch_number': item.batch_number,
            })

        giv = self.inventory_service.create_goods_issue_voucher(
            warehouse_id=transfer.source_warehouse_id,
            items=[
                {
                    'product_id': it['product_id'],
                    'quantity': it['quantity'],
                    'batch_number': it.get('batch_number'),
                }
                for it in items_data
            ],
            reference_type='Transfer',
            reference_id=transfer.id,
            notes=f'Auto-generated GIV for transfer {transfer.transfer_number}',
            created_by_id=issued_by_id,
            issued_by_id=issued_by_id,
        )

        self.inventory_service.process_goods_issue(giv.id, issued_by_id)

        transfer.status = 'Issued'
        transfer.giv_id = giv.id
        return self.repo.update(transfer)

    def receive_goods(
        self,
        transfer_id: int,
        received_by_id: Optional[int] = None,
    ) -> Transfer:
        transfer = self.get_transfer(transfer_id)

        if transfer.status != 'Issued':
            raise ValidationError(
                f'Goods must be issued before receiving. Current status: {transfer.status}'
            )

        items_data = []
        for item in transfer.items:
            quantity = float(item.quantity)
            items_data.append({
                'product_id': item.product_id,
                'quantity': quantity,
                'unit_cost': float(item.unit_cost) if item.unit_cost else None,
                'batch_number': item.batch_number,
            })

        grv = self.inventory_service.create_goods_receive_voucher(
            warehouse_id=transfer.destination_warehouse_id,
            items=[
                {
                    'product_id': it['product_id'],
                    'quantity': it['quantity'],
                    'unit_cost': it.get('unit_cost'),
                    'batch_number': it.get('batch_number'),
                }
                for it in items_data
            ],
            reference_type='Transfer',
            reference_id=transfer.id,
            notes=f'Auto-generated GRV for transfer {transfer.transfer_number}',
            created_by_id=received_by_id,
            received_by_id=received_by_id,
        )

        self.inventory_service.process_goods_receipt(grv.id, received_by_id)

        transfer.status = 'Completed'
        transfer.grv_id = grv.id
        transfer.received_by_id = received_by_id
        transfer.received_at = datetime.utcnow()
        return self.repo.update(transfer)
