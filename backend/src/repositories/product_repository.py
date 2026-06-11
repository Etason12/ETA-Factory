from decimal import Decimal
from typing import Optional

from models.models import Product
from repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self) -> None:
        super().__init__(Product)

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return Product.query.filter(
            Product.sku == sku,
            Product.is_deleted == False,
        ).first()

    def get_by_category(self, category_id: int) -> list[Product]:
        return Product.query.filter(
            Product.category_id == category_id,
            Product.is_deleted == False,
        ).all()

    def get_by_unit(self, unit_id: int) -> list[Product]:
        return Product.query.filter(
            Product.unit_id == unit_id,
            Product.is_deleted == False,
        ).all()

    def get_active(self) -> list[Product]:
        return Product.query.filter(
            Product.is_active == True,
            Product.is_deleted == False,
        ).all()

    def get_by_name(self, name: str) -> Optional[Product]:
        return Product.query.filter(
            Product.name == name,
            Product.is_deleted == False,
        ).first()

    def get_by_price_range(self, min_price: Decimal, max_price: Decimal) -> list[Product]:
        return Product.query.filter(
            Product.unit_price.between(min_price, max_price),
            Product.is_deleted == False,
        ).all()

    def search(self, term: str) -> list[Product]:
        pattern = f'%{term}%'
        return Product.query.filter(
            Product.is_deleted == False,
            (
                Product.name.ilike(pattern) |
                Product.sku.ilike(pattern) |
                Product.description.ilike(pattern)
            ),
        ).all()

    def get_low_stock(self, threshold: Decimal = Decimal('10')) -> list[Product]:
        from models.models import Inventory
        return Product.query.join(
            Inventory, Inventory.product_id == Product.id,
        ).filter(
            Product.is_deleted == False,
            Inventory.quantity_on_hand <= threshold,
        ).all()
