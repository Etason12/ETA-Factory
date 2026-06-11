from datetime import date
from typing import Any, Optional

from models.models import (
    GoodsIssueVoucher,
    GoodsReceiveVoucher,
    LoadingAuthorization,
    ReturnVoucher,
    StockAdjustment,
    Transfer,
    Warehouse,
)
from repositories.base import BaseRepository


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

    def get_by_type(self, type: str) -> list[Warehouse]:
        return Warehouse.query.filter(
            Warehouse.type == type,
            Warehouse.is_deleted == False,
        ).all()

    def get_active(self) -> list[Warehouse]:
        return Warehouse.query.filter(
            Warehouse.is_active == True,
            Warehouse.is_deleted == False,
        ).all()

    def search(self, term: str) -> list[Warehouse]:
        pattern = f'%{term}%'
        return Warehouse.query.filter(
            Warehouse.is_deleted == False,
            (
                Warehouse.name.ilike(pattern) |
                Warehouse.code.ilike(pattern)
            ),
        ).all()


class GRVRepository(BaseRepository[GoodsReceiveVoucher]):
    def __init__(self) -> None:
        super().__init__(GoodsReceiveVoucher)

    def get_by_voucher_number(self, voucher_number: str) -> Optional[GoodsReceiveVoucher]:
        return GoodsReceiveVoucher.query.filter_by(voucher_number=voucher_number).first()

    def get_by_warehouse(self, warehouse_id: int) -> list[GoodsReceiveVoucher]:
        return GoodsReceiveVoucher.query.filter_by(warehouse_id=warehouse_id).all()

    def get_by_status(self, status: str) -> list[GoodsReceiveVoucher]:
        return GoodsReceiveVoucher.query.filter_by(status=status).all()

    def get_by_reference(self, reference_type: str, reference_id: int) -> list[GoodsReceiveVoucher]:
        return GoodsReceiveVoucher.query.filter(
            GoodsReceiveVoucher.reference_type == reference_type,
            GoodsReceiveVoucher.reference_id == reference_id,
        ).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[GoodsReceiveVoucher]:
        return GoodsReceiveVoucher.query.filter(
            GoodsReceiveVoucher.voucher_date.between(start_date, end_date),
        ).all()

    def get_pending(self) -> list[GoodsReceiveVoucher]:
        return GoodsReceiveVoucher.query.filter(
            GoodsReceiveVoucher.status.in_(['Draft', 'Pending']),
        ).all()


class GIVRepository(BaseRepository[GoodsIssueVoucher]):
    def __init__(self) -> None:
        super().__init__(GoodsIssueVoucher)

    def get_by_voucher_number(self, voucher_number: str) -> Optional[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter_by(voucher_number=voucher_number).first()

    def get_by_warehouse(self, warehouse_id: int) -> list[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter_by(warehouse_id=warehouse_id).all()

    def get_by_status(self, status: str) -> list[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter_by(status=status).all()

    def get_by_sales_order(self, sales_order_id: int) -> list[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter_by(sales_order_id=sales_order_id).all()

    def get_by_reference(self, reference_type: str, reference_id: int) -> list[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter(
            GoodsIssueVoucher.reference_type == reference_type,
            GoodsIssueVoucher.reference_id == reference_id,
        ).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter(
            GoodsIssueVoucher.voucher_date.between(start_date, end_date),
        ).all()

    def get_pending(self) -> list[GoodsIssueVoucher]:
        return GoodsIssueVoucher.query.filter(
            GoodsIssueVoucher.status.in_(['Draft', 'Pending']),
        ).all()


class TransferRepository(BaseRepository[Transfer]):
    def __init__(self) -> None:
        super().__init__(Transfer)

    def get_by_transfer_number(self, transfer_number: str) -> Optional[Transfer]:
        return Transfer.query.filter_by(transfer_number=transfer_number).first()

    def get_by_source_warehouse(self, warehouse_id: int) -> list[Transfer]:
        return Transfer.query.filter_by(source_warehouse_id=warehouse_id).all()

    def get_by_destination_warehouse(self, warehouse_id: int) -> list[Transfer]:
        return Transfer.query.filter_by(destination_warehouse_id=warehouse_id).all()

    def get_by_status(self, status: str) -> list[Transfer]:
        return Transfer.query.filter_by(status=status).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[Transfer]:
        return Transfer.query.filter(
            Transfer.transfer_date.between(start_date, end_date),
        ).all()

    def get_pending(self) -> list[Transfer]:
        return Transfer.query.filter(
            Transfer.status.in_(['Draft', 'Pending', 'In Transit']),
        ).all()

    def get_completed(self) -> list[Transfer]:
        return Transfer.query.filter_by(status='Completed').all()


class LoadingAuthorizationRepository(BaseRepository[LoadingAuthorization]):
    def __init__(self) -> None:
        super().__init__(LoadingAuthorization)

    def get_by_authorization_number(self, authorization_number: str) -> Optional[LoadingAuthorization]:
        return LoadingAuthorization.query.filter_by(authorization_number=authorization_number).first()

    def get_by_sales_order(self, sales_order_id: int) -> list[LoadingAuthorization]:
        return LoadingAuthorization.query.filter_by(sales_order_id=sales_order_id).all()

    def get_by_warehouse(self, warehouse_id: int) -> list[LoadingAuthorization]:
        return LoadingAuthorization.query.filter_by(warehouse_id=warehouse_id).all()

    def get_by_status(self, status: str) -> list[LoadingAuthorization]:
        return LoadingAuthorization.query.filter_by(status=status).all()

    def get_pending(self) -> list[LoadingAuthorization]:
        return LoadingAuthorization.query.filter_by(status='Pending').all()


class StockAdjustmentRepository(BaseRepository[StockAdjustment]):
    def __init__(self) -> None:
        super().__init__(StockAdjustment)

    def get_by_adjustment_number(self, adjustment_number: str) -> Optional[StockAdjustment]:
        return StockAdjustment.query.filter_by(adjustment_number=adjustment_number).first()

    def get_by_warehouse(self, warehouse_id: int) -> list[StockAdjustment]:
        return StockAdjustment.query.filter_by(warehouse_id=warehouse_id).all()

    def get_by_status(self, status: str) -> list[StockAdjustment]:
        return StockAdjustment.query.filter_by(status=status).all()

    def get_by_type(self, adjustment_type: str) -> list[StockAdjustment]:
        return StockAdjustment.query.filter_by(adjustment_type=adjustment_type).all()

    def get_pending(self) -> list[StockAdjustment]:
        return StockAdjustment.query.filter(
            StockAdjustment.status.in_(['Draft', 'Pending']),
        ).all()


class ReturnVoucherRepository(BaseRepository[ReturnVoucher]):
    def __init__(self) -> None:
        super().__init__(ReturnVoucher)

    def get_by_return_number(self, return_number: str) -> Optional[ReturnVoucher]:
        return ReturnVoucher.query.filter_by(return_number=return_number).first()

    def get_by_warehouse(self, warehouse_id: int) -> list[ReturnVoucher]:
        return ReturnVoucher.query.filter_by(warehouse_id=warehouse_id).all()

    def get_by_customer(self, customer_id: int) -> list[ReturnVoucher]:
        return ReturnVoucher.query.filter_by(customer_id=customer_id).all()

    def get_by_status(self, status: str) -> list[ReturnVoucher]:
        return ReturnVoucher.query.filter_by(status=status).all()

    def get_by_type(self, return_type: str) -> list[ReturnVoucher]:
        return ReturnVoucher.query.filter_by(return_type=return_type).all()

    def get_pending(self) -> list[ReturnVoucher]:
        return ReturnVoucher.query.filter(
            ReturnVoucher.status.in_(['Draft', 'Pending']),
        ).all()
