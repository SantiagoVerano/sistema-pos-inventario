"""
Pruebas Unitarias para las Reglas de Negocio del Módulo de Ventas y POS (VentaService).
"""

from decimal import Decimal
import unittest
from app.core.exceptions import ValidationException
from app.services.ventas.venta_service import VentaService


class TestVentaService(unittest.TestCase):
    """Casos de prueba para validaciones y reglas financieras del motor de ventas."""

    def setUp(self) -> None:
        self.venta_service = VentaService()

    def test_procesar_venta_sin_items_lanza_excepcion(self) -> None:
        """Una venta en POS no puede procesarse con el carrito vacío."""
        with self.assertRaises(ValidationException) as ctx:
            self.venta_service.procesar_venta(
                id_usuario_cajero=1,
                items=[],
                descuento=Decimal("0.00")
            )
        self.assertIn("al menos un producto", str(ctx.exception))

    def test_procesar_venta_descuento_negativo_lanza_excepcion(self) -> None:
        """No se permiten descuentos negativos en la transacción."""
        with self.assertRaises(ValidationException) as ctx:
            self.venta_service.procesar_venta(
                id_usuario_cajero=1,
                items=[{"id_producto": 1, "cantidad": 1}],
                descuento=Decimal("-5.00")
            )
        self.assertIn("no puede ser un valor negativo", str(ctx.exception))

    def test_anular_venta_motivo_invalido_lanza_excepcion(self) -> None:
        """La anulación de una venta exige un motivo justificado mínimo de 3 caracteres."""
        with self.assertRaises(ValidationException) as ctx:
            self.venta_service.anular_venta(
                id_venta=10,
                id_usuario_supervisor=1,
                motivo="  "
            )
        self.assertIn("motivo justificado", str(ctx.exception))

    def test_registrar_cliente_documento_vacio_lanza_excepcion(self) -> None:
        """El número de identificación del cliente no puede ser una cadena vacía."""
        with self.assertRaises(ValidationException) as ctx:
            self.venta_service.registrar_cliente(
                numero_documento="   ",
                nombre="Juan Perez"
            )
        self.assertIn("documento del cliente es obligatorio", str(ctx.exception))

    def test_registrar_cliente_nombre_vacio_lanza_excepcion(self) -> None:
        """El nombre del cliente no puede ser una cadena vacía."""
        with self.assertRaises(ValidationException) as ctx:
            self.venta_service.registrar_cliente(
                numero_documento="12345678",
                nombre="   "
            )
        self.assertIn("nombre del cliente es obligatorio", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
