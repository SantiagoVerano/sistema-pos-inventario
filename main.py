"""
Punto de Entrada Principal de la Aplicación de Escritorio (main.py)

Responsabilidad Arquitectónica:
-------------------------------
Inicializar la aplicación PySide6, verificar esquemas de base de datos PostgreSQL,
garantizar la existencia del usuario administrador por defecto y lanzar el ciclo de
vida gráfico comenzando en 'LoginWindow'.
"""

import sys
from decimal import Decimal
from PySide6.QtWidgets import QApplication

from app.core.config import settings
from app.core.logger import get_logger
from app.database.base import Base
from app.database.connection import engine, inicializar_esquemas_db, session_scope
import app.database.models

from app.database.repositories.seguridad.usuario_repository import UsuarioRepository
from app.database.repositories.seguridad.rol_repository import RolRepository
from app.database.repositories.inventario.categoria_repository import CategoriaRepository
from app.database.repositories.inventario.unidad_repository import UnidadRepository
from app.database.repositories.inventario.producto_repository import ProductoRepository
from app.database.repositories.inventario.stock_repository import StockRepository
from app.database.repositories.inventario.movimiento_repository import MovimientoRepository

from app.services.seguridad.auth_service import AuthService, UsuarioAutenticado
from app.ui.windows.login_window import LoginWindow
from app.ui.windows.main_window import MainWindow

logger = get_logger(__name__)


def inicializar_sistema() -> None:
    """Verifica esquemas y siembra datos iniciales de prueba en PostgreSQL."""
    logger.info("Inicializando esquemas y tablas en PostgreSQL...")
    inicializar_esquemas_db()
    Base.metadata.create_all(bind=engine)

    # Sembrar usuario administrador inicial y datos demo
    auth_service = AuthService()
    with session_scope() as session:
        repo_usuario = UsuarioRepository(session)
        repo_rol = RolRepository(session)
        repo_cat = CategoriaRepository(session)
        repo_uni = UnidadRepository(session)
        repo_prod = ProductoRepository(session)
        repo_stock = StockRepository(session)
        repo_mov = MovimientoRepository(session)

        # 1. Rol Administrador
        rol_admin = repo_rol.obtener_por_nombre("ADMINISTRADOR")
        if not rol_admin:
            rol_admin = repo_rol.create(
                app.database.models.seguridad.Rol(nombre="ADMINISTRADOR")
            )

        # 2. Usuario Administrador por Defecto
        admin_user = repo_usuario.obtener_por_correo("admin@pos.com")
        if not admin_user:
            admin_user = repo_usuario.create(
                app.database.models.seguridad.Usuario(
                    nombre="Administrador Sistema",
                    correo="admin@pos.com",
                    password_hash=auth_service.hashear_password("admin123"),
                    activo=True,
                )
            )
            repo_usuario.asignar_rol(admin_user.id_usuario, rol_admin.id_rol)
            logger.info("Usuario inicial creado: admin@pos.com / clave: admin123")

        # 3. Categoría y Unidad demo
        cat_demo = repo_cat.obtener_por_nombre("Bebidas y Alimentos")
        if not cat_demo:
            cat_demo = repo_cat.create(
                app.database.models.inventario.Categoria(
                    nombre="Bebidas y Alimentos",
                    descripcion="Productos comestibles y bebidas",
                    estado=True,
                )
            )

        uni_demo = repo_uni.obtener_por_nombre("Unidad")
        if not uni_demo:
            uni_demo = repo_uni.create(
                app.database.models.inventario.Unidad(
                    nombre="Unidad",
                    abreviatura="UND",
                )
            )

        # 4. Producto Demo para POS
        prod_demo = repo_prod.obtener_por_sku("PROD-COCA-COLA")
        if not prod_demo:
            prod_demo = repo_prod.create(
                app.database.models.inventario.Producto(
                    codigo_barras="775123456001",
                    sku="PROD-COCA-COLA",
                    nombre="Gaseosa Coca-Cola 500ml",
                    descripcion="Bebida refrescante personal",
                    id_categoria=cat_demo.id_categoria,
                    id_unidad=uni_demo.id_unidad,
                    precio_compra=Decimal("1.20"),
                    precio_venta=Decimal("2.50"),
                    stock_minimo=10,
                    activo=True,
                )
            )
            repo_stock.inicializar_stock(prod_demo.id_producto, 50)
            repo_mov.registrar_movimiento(
                id_producto=prod_demo.id_producto,
                tipo_movimiento="ENTRADA",
                cantidad=50,
                id_usuario=admin_user.id_usuario,
                referencia="INVENTARIO_INICIAL",
                observacion="Stock inicial para pruebas de POS",
            )
            logger.info("Producto demo 'Coca-Cola' creado con 50 unidades de stock.")


class AppManager:
    """Administra la navegación entre la ventana de Login y la Ventana Principal."""

    def __init__(self) -> None:
        self.login_window: Optional[LoginWindow] = None
        self.main_window: Optional[MainWindow] = None

    def mostrar_login(self) -> None:
        self.login_window = LoginWindow()
        self.login_window.usuario_autenticado.connect(self.mostrar_principal)
        self.login_window.show()

    def mostrar_principal(self, usuario: UsuarioAutenticado) -> None:
        self.main_window = MainWindow(usuario=usuario)
        self.main_window.sesion_cerrada.connect(self.mostrar_login)
        self.main_window.show()


def main() -> None:
    """Punto de entrada de ejecución del proceso Qt."""
    app = QApplication(sys.argv)
    app.setApplicationName(settings.APP_NAME)
    app.setApplicationVersion(settings.APP_VERSION)

    try:
        inicializar_sistema()
    except Exception as exc:
        logger.warning(
            f"No se pudo conectar a PostgreSQL al arrancar (la app iniciará pero requerirá conexión): {exc}"
        )

    manager = AppManager()
    manager.mostrar_login()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
