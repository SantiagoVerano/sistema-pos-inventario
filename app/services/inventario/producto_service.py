from typing import List
from app.database.models.inventario.producto import Producto
from app.database.repositories.inventario.producto_repository import ProductoRepositoryInterface

class ProductoService:
    def __init__(self, repository: ProductoRepositoryInterface):
        self.repository = repository

    def get_productos(self) -> List[Producto]:
        return self.repository.get_productos()

    def add_producto(self, producto: Producto) -> None:
        self.repository.add_producto(producto)
