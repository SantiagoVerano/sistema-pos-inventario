from typing import List, Optional
from app.services.inventario.producto_service import ProductoService
from app.database.models.inventario.producto import Producto

class ProductoController:
    def __init__(self):
        self.service = ProductoService()

    def get_productos(self) -> List[Producto]:
        return self.service.get_productos()

    def add_producto(self, nombre: str, precio: float) -> None:
        producto = Producto(nombre=nombre, precio=precio)
        self.service.add_producto(producto)

    def get_producto_by_id(self, producto_id: int) -> Optional[Producto]:
        return self.service.get_producto_by_id(producto_id)

    def update_producto(self, producto_id: int, nombre: str, precio: float) -> None:
        producto_data = {"nombre": nombre, "precio": precio}
        self.service.update_producto(producto_id, producto_data)

    def delete_producto(self, producto_id: int) -> bool:
        return self.service.delete_producto(producto_id)

    def get_productos_by_category(self, category: str) -> List[Producto]:
        return self.service.get_productos_by_category(category)