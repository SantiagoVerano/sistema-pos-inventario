# 🛒 CorePOS - Sistema Empresarial de Punto de Venta e Inventarios

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt)-41CD52?logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![ORM](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Migrations](https://img.shields.io/badge/Migrations-Alembic-FF6F00)](https://alembic.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-Unittest%20%7C%20Pytest-brightgreen)](https://docs.pytest.org/)

Sistema de escritorio de alto rendimiento para la gestión integral de ventas, control perpetuo de inventario, compras y seguridad multiusuario, diseñado bajo principios de **Clean Architecture**, alta integridad referencial y control estricto de concurrencia.

---

## Arquitectura y Patrones de Diseño

El sistema está estructurado desacoplando responsabilidades en capas independientes:

```text
PROYECTO/
├── alembic/                # Control de versiones y migraciones de BD
├── app/
│   ├── core/               # Configuración (Pydantic v2), constantes, excepciones y logging
│   ├── database/           # Modelos SQLAlchemy 2.0 y Repositorios (Patrón Repository)
│   │   ├── models/         # 4 Esquemas: seguridad, inventario, compras, ventas
│   │   └── repositories/   # Abstracción de acceso a datos y consultas optimizadas
│   ├── services/           # Lógica de Negocio y Unit of Work (session_scope ACID)
│   ├── controllers/        # Orquestación entre UI y Capa de Servicios
│   └── ui/                 # Vistas interactivas PySide6, temas QSS y ventanas modales
├── tests/                  # Suite de pruebas unitarias automatizadas
├── main.py                 # Ciclo de vida principal y arranque de la aplicación
└── requirements.txt        # Dependencias fijadas del ecosistema
```

### Principales Decisiones Técnicas de Ingeniería:

1. **Prevención de Concurrencia y Stock Negativo:**
   - Implementación de **Bloqueo Pesimista (Pessimistic Locking)** con `SELECT ... FOR UPDATE` en [stock_repository.py](file:///c:/Users/Xvers/Documents/001_UCC/PROYECTOS_PERSONALES/SISTEMA_POS/PROYECTO/app/database/repositories/inventario/stock_repository.py). Evita condiciones de carrera (*race conditions*) cuando múltiples terminales de caja facturan el último artículo disponible simultáneamente.
2. **Kardex Perpetuo Inmutable:**
   - Toda alteración en el stock (despacho por venta, anulación con reintegro, ingreso por compra o ajuste físico) genera un registro inmutable en `inventario.movimientos_inventario` para auditoría contable transparente.
3. **Segregación Multi-Esquema en PostgreSQL:**
   - La base de datos está organizada en 4 esquemas desacoplados: `seguridad`, `inventario`, `compras` y `ventas`, facilitando gobernanza de datos y escalabilidad futura hacia microservicios.
4. **Patrón Unit of Work y Transacciones ACID:**
   - Context manager `session_scope()` que garantiza atomicidad: cualquier excepción durante una transacción realiza `rollback` automático protegiendo el estado de la base de datos.
5. **Seguridad y Control de Acceso (RBAC):**
   - Hashing criptográfico de credenciales mediante **Argon2** (con fallback estándar a PBKDF2-HMAC-SHA256 con salt de 100,000 iteraciones).

---

## Módulos Funcionales

* **Terminal Punto de Venta (POS):** Búsqueda rápida por lector láser de código de barras / SKU, cliente genérico rápido ("Consumidor Final"), carrito reactivo, aplicación de descuentos validados y cálculo de cambio/vuelto en tiempo real.
* **Inventario & Bodega:** Control de stock mínimo, gestión de categorías, marcas, unidades de medida y ajustes de almacén con registro de responsable.
* **Compras & Proveedores:** Registro de facturas de compra a proveedores con actualización automática de stock de costo.
* **Historial de Ventas:** Visualización de ventas por fecha/cajero, reimpresión de comprobantes y anulación supervisada con devolución física a stock.
* **Seguridad & Usuarios:** Gestión de operadores de caja, administradores y asignación de roles.

---

## Instalación y Puesta en Marcha

### Prerrequisitos
* Python 3.12 o 3.13 instalado.
* PostgreSQL 15+ ejecutándose localmente o en contenedor.

### 1. Clonar el Repositorio y Crear el Entorno Virtual
```bash
git clone https://github.com/TU_USUARIO/sistema-pos-inventario.git
cd sistema-pos-inventario

python -m venv env
# En Windows (PowerShell):
.\env\Scripts\Activate.ps1
# En Linux / macOS:
source env/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Copia la plantilla `.env.example` y crea tu archivo `.env`:
```bash
cp .env.example .env
```
Edita `.env` con tus credenciales de PostgreSQL:
```env
DATABASE_URL=postgresql+psycopg2://postgres:tu_password@localhost:5432/corelytics
```

### 4. Ejecutar Migraciones de Base de Datos
```bash
alembic upgrade head
```

### 5. Lanzar la Aplicación
```bash
python main.py
```
> **Credenciales de prueba por defecto:**
> * **Usuario:** `admin@pos.com`
> * **Contraseña:** `admin123`

---

## Ejecución de Pruebas Unitarias

Para validar las reglas de negocio, integridad de hashing y cálculos financieros:

```bash
python -m unittest discover tests
```
O usando pytest:
```bash
pytest
```

---

## Licencia y Uso Comercial

Este proyecto está bajo la licencia **GNU AGPLv3** (o GPLv3).

### Para Reclutadores y Desarrolladores:
* **Si estás evaluando mi perfil:** Siéntete libre de clonar, ejecutar, revisar la arquitectura y probar el código en tu entorno local. ¡Este repositorio fue creado precisamente para demostrar mis habilidades técnicas!

### Nota sobre el Futuro Comercial (Licencia Dual):
Como creador y titular único de los derechos de autor de este código fuente, me reservo el derecho de cambiar o vender este software bajo una **licencia comercial privada** en el futuro. 

Bajo los términos actuales de la AGPLv3, cualquier persona o empresa puede usar este código, **pero si lo modifican o lo incluyen en un producto comercial (incluidos servicios en la nube), están obligados por ley a liberar todo el código fuente de su plataforma**. Si deseas utilizar este proyecto en un entorno comercial cerrado sin liberar tu propio código, por favor contáctame para negociar una licencia comercial privada.

