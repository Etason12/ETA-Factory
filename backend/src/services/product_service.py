from typing import Any, Optional

from models.models import Product, ProductCategory, Unit
from repositories.base import BaseRepository
from utils.error_handlers import ConflictError, NotFoundError, ValidationError


class ProductRepository(BaseRepository[Product]):
    def __init__(self) -> None:
        super().__init__(Product)

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return Product.query.filter(
            Product.sku == sku,
            Product.is_deleted == False,
        ).first()

    def search(self, term: str) -> list[Product]:
        pattern = f'%{term}%'
        return Product.query.filter(
            Product.is_deleted == False,
            (Product.name.ilike(pattern) | Product.sku.ilike(pattern)),
        ).all()

    def get_by_category(self, category_id: int) -> list[Product]:
        return Product.query.filter(
            Product.category_id == category_id,
            Product.is_deleted == False,
        ).all()


class ProductCategoryRepository(BaseRepository[ProductCategory]):
    def __init__(self) -> None:
        super().__init__(ProductCategory)

    def get_by_name(self, name: str) -> Optional[ProductCategory]:
        return ProductCategory.query.filter(
            ProductCategory.name == name,
            ProductCategory.is_deleted == False,
        ).first()


class UnitRepository(BaseRepository[Unit]):
    def __init__(self) -> None:
        super().__init__(Unit)

    def get_by_name(self, name: str) -> Optional[Unit]:
        return Unit.query.filter(Unit.name == name).first()

    def get_by_abbreviation(self, abbreviation: str) -> Optional[Unit]:
        return Unit.query.filter(Unit.abbreviation == abbreviation).first()


class ProductService:
    def __init__(
        self,
        product_repository: Optional[ProductRepository] = None,
        category_repository: Optional[ProductCategoryRepository] = None,
        unit_repository: Optional[UnitRepository] = None,
    ):
        self.repo = product_repository or ProductRepository()
        self.category_repo = category_repository or ProductCategoryRepository()
        self.unit_repo = unit_repository or UnitRepository()

    def get_product(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundError('Product not found')
        return product

    def get_products(
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

    def create_product(
        self,
        sku: str,
        name: str,
        category_id: int,
        unit_id: int,
        unit_price: float = 0,
        cost_price: float = 0,
        description: Optional[str] = None,
    ) -> Product:
        if not sku or not sku.strip():
            raise ValidationError('SKU is required')
        if not name or not name.strip():
            raise ValidationError('Product name is required')

        if self.repo.get_by_sku(sku):
            raise ConflictError(f'SKU "{sku}" already exists')

        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise ValidationError('Category not found')

        unit = self.unit_repo.get_by_id(unit_id)
        if not unit:
            raise ValidationError('Unit not found')

        product = Product(
            sku=sku.strip().upper(),
            name=name.strip(),
            description=description,
            unit_price=unit_price,
            cost_price=cost_price,
            category_id=category_id,
            unit_id=unit_id,
            is_active=True,
        )
        return self.repo.create(product)

    def update_product(
        self,
        product_id: int,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        unit_price: Optional[float] = None,
        cost_price: Optional[float] = None,
        category_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Product:
        product = self.get_product(product_id)

        if sku is not None:
            if not sku.strip():
                raise ValidationError('SKU cannot be empty')
            sku_upper = sku.strip().upper()
            existing = self.repo.get_by_sku(sku_upper)
            if existing and existing.id != product_id:
                raise ConflictError(f'SKU "{sku}" already exists')
            product.sku = sku_upper

        if name is not None:
            if not name.strip():
                raise ValidationError('Product name cannot be empty')
            product.name = name.strip()
        if description is not None:
            product.description = description
        if unit_price is not None:
            product.unit_price = unit_price
        if cost_price is not None:
            product.cost_price = cost_price
        if category_id is not None:
            category = self.category_repo.get_by_id(category_id)
            if not category:
                raise ValidationError('Category not found')
            product.category_id = category_id
        if unit_id is not None:
            unit = self.unit_repo.get_by_id(unit_id)
            if not unit:
                raise ValidationError('Unit not found')
            product.unit_id = unit_id
        if is_active is not None:
            product.is_active = is_active

        return self.repo.update(product)

    def delete_product(self, product_id: int) -> None:
        product = self.get_product(product_id)
        self.repo.delete(product)


class ProductCategoryService:
    def __init__(
        self, repository: Optional[ProductCategoryRepository] = None
    ):
        self.repo = repository or ProductCategoryRepository()

    def get_category(self, category_id: int) -> ProductCategory:
        category = self.repo.get_by_id(category_id)
        if not category:
            raise NotFoundError('Category not found')
        return category

    def get_categories(
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

    def create_category(self, name: str, description: Optional[str] = None) -> ProductCategory:
        if not name or not name.strip():
            raise ValidationError('Category name is required')
        if self.repo.get_by_name(name):
            raise ConflictError(f'Category "{name}" already exists')
        category = ProductCategory(name=name.strip(), description=description)
        return self.repo.create(category)

    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ProductCategory:
        category = self.get_category(category_id)
        if name is not None:
            if not name.strip():
                raise ValidationError('Category name cannot be empty')
            existing = self.repo.get_by_name(name)
            if existing and existing.id != category_id:
                raise ConflictError(f'Category "{name}" already exists')
            category.name = name.strip()
        if description is not None:
            category.description = description
        return self.repo.update(category)

    def delete_category(self, category_id: int) -> None:
        category = self.get_category(category_id)
        self.repo.delete(category)


class UnitService:
    def __init__(self, repository: Optional[UnitRepository] = None):
        self.repo = repository or UnitRepository()

    def get_unit(self, unit_id: int) -> Unit:
        unit = self.repo.get_by_id(unit_id)
        if not unit:
            raise NotFoundError('Unit not found')
        return unit

    def get_units(
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

    def create_unit(self, name: str, abbreviation: str) -> Unit:
        if not name or not name.strip():
            raise ValidationError('Unit name is required')
        if not abbreviation or not abbreviation.strip():
            raise ValidationError('Abbreviation is required')
        if self.repo.get_by_name(name):
            raise ConflictError(f'Unit "{name}" already exists')
        unit = Unit(name=name.strip(), abbreviation=abbreviation.strip())
        return self.repo.create(unit)

    def update_unit(
        self,
        unit_id: int,
        name: Optional[str] = None,
        abbreviation: Optional[str] = None,
    ) -> Unit:
        unit = self.get_unit(unit_id)
        if name is not None:
            if not name.strip():
                raise ValidationError('Unit name cannot be empty')
            existing = self.repo.get_by_name(name)
            if existing and existing.id != unit_id:
                raise ConflictError(f'Unit "{name}" already exists')
            unit.name = name.strip()
        if abbreviation is not None:
            unit.abbreviation = abbreviation.strip()
        return self.repo.update(unit)

    def delete_unit(self, unit_id: int) -> None:
        unit = self.get_unit(unit_id)
        self.repo.delete(unit)
