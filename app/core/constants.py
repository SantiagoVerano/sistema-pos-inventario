"""
Módulo de Constantes y Enumeraciones del Dominio (app/core/constants.py)

Responsabilidad Arquitectónica:
-------------------------------
Centralizar todas las constantes, identificadores de esquemas y tipos enumerados (Enum)
del sistema exactamente alineados con los CheckConstraints del script DDL de PostgreSQL.
"""

from enum import Enum


# ==============================================================================
# 1. ESQUEMAS DE BASE DE DATOS POSTGRESQL
# ==============================================================================
class DatabaseSchema(str, Enum):
    """Nombres exactos de los 4 esquemas independientes en PostgreSQL."""
    SEGURIDAD = "seguridad"
    INVENTARIO = "inventario"
    COMPRAS = "compras"
    VENTAS = "ventas"


# ==============================================================================
# 2. CONSTANTES DE DOMINIO: INVENTARIO Y KARDEX
# ==============================================================================
class TipoMovimiento(str, Enum):
    """
    Tipos de movimiento de Kardex permitidos por la base de datos:
    CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION'))
    """
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
    DEVOLUCION = "DEVOLUCION"


# ==============================================================================
# 3. CONSTANTES DE DOMINIO: COMPRAS
# ==============================================================================
class EstadoCompra(str, Enum):
    """
    Estados de la transacción de compra:
    CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA'))
    """
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"


# ==============================================================================
# 4. CONSTANTES DE DOMINIO: VENTAS
# ==============================================================================
class EstadoVenta(str, Enum):
    """
    Estados de la transacción de venta:
    CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA'))
    """
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"
