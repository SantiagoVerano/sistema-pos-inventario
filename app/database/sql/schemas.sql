
-- =====================================================================
-- SCRIPT DE INICIALIZACIÓN DE LA BASE DE DATOS (GESTION DE INVENTARIOS)
-- Autor: SANTIAGO ESTEBAN VERANO CASTELLANOS
-- =====================================================================

-- =====================================================================
-- NOTA ARQUITECTÓNICA DE DISEÑO:
-- Actualmente se utiliza TIMESTAMP (sin zona horaria) debido a que la 
-- aplicación está diseñada para desplegarse y ejecutarse en entornos locales. 
-- Para un entorno de producción global/distribuido (ej. AWS, Render), 
-- la mejor práctica recomendada es migrar estos campos a TIMESTAMPTZ 
-- para evitar desfases horarios entre el servidor de base de datos y el backend.
-- =====================================================================

-- 0. CREACIÓN DE BASE DE DATOS (TEMPLATE PARA DESPLEGAR VARIOS PROYECTOS BAJO ESTA ESTRUCTURA)

CREATE DATABASE gestion_inventarios
    WITH
        ENCODING = 'UTF8'
        IS_TEMPLATE = 'TRUE'; -- Esto es lo que permite que se pueda clonar la base de datos 
                              -- para crear nuevos proyectos con la misma estructura.

-- 1. CREACIÓN DE ESQUEMAS LÓGICOS

CREATE SCHEMA seguridad;

CREATE SCHEMA inventario;

CREATE SCHEMA compras;

CREATE SCHEMA ventas;

-- 2. CONFIGURACIÓN DEL SEARCH_PATH
-- Esto se usa principalmente para que al hacer consultas dentro del entorno psql
-- no sea necesario especificar el esquema de cada tabla.

SET SEARCH_PATH TO seguridad, inventario, compras, ventas, public;

-- ==================================================
-- CREACIÓN DE LAS TABLAS MAESTRAS (SIN DEPENDENCIAS)
-- ==================================================

-- CREACIÓN DE LA TABLA categorias EN EL SCHEMA inventario

CREATE TABLE inventario.categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CREACIÓN DE LA TABLA marcas EN EL SCHEMA inventario

CREATE TABLE inventario.marcas (
    id_marca SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    estado BOOLEAN DEFAULT TRUE
);

-- CREACION DE LA TABLA unidades EN EL SCHEMA inventario

CREATE TABLE inventario.unidades (
    id_unidad SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    abreviatura VARCHAR(10)
);

-- CREACION DE LA TABLA roles EN EL SCHEMA seguridad

CREATE TABLE seguridad.roles (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- CREACION DE LA TABLA usuarios EN EL SCHEMA seguridad

CREATE TABLE seguridad.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CREACION DE LA TABLA clientes EN EL SCHEMA ventas

CREATE TABLE ventas.clientes (
    id_cliente SERIAL PRIMARY KEY,
    tipo_documento VARCHAR(20),
    numero_documento VARCHAR(50),
    nombre VARCHAR(150),
    apellido VARCHAR(150),
    telefono VARCHAR(50),
    correo VARCHAR(150),
    direccion TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CREACION DE LA TABLA proveedores EN EL SCHEMA compras

CREATE TABLE compras.proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    razon_social VARCHAR(250) NOT NULL,
    nit VARCHAR(50),
    telefono VARCHAR(50),
    correo VARCHAR(150),
    direccion TEXT,
    estado BOOLEAN DEFAULT TRUE
);

-- ========================================
-- CREACIÓN DE LAS TABLAS DE SEGUNDO NIVEL
-- ========================================

-- CREACIÓN DE LA TABLA usuario_rol EN EL SCHEMA seguridad
-- (TABLA INTERMEDIA PARA EVITAR RELACION MUCHOS A MUCHOS)

CREATE TABLE seguridad.usuario_rol (
    id_usuario INT NOT NULL,
    id_rol INT NOT NULL,
    
    -- Definimos la llave primaria compuesta
    PRIMARY KEY (id_usuario, id_rol),
    
    -- Definimos las llaves foráneas que se conectan a las tablas de arriba
    CONSTRAINT fk_usuariorol_usuario 
        FOREIGN KEY (id_usuario) 
        REFERENCES seguridad.usuarios(id_usuario) 
        ON DELETE CASCADE,
        
    CONSTRAINT fk_usuariorol_rol 
        FOREIGN KEY (id_rol) 
        REFERENCES seguridad.roles(id_rol) 
        ON DELETE RESTRICT
);

-- CREACIÓN DE LA TABLA productos EN EL SCHEMA inventario

CREATE TABLE inventario.productos (
    id_producto SERIAL PRIMARY KEY,
    codigo_barras VARCHAR(50) UNIQUE,
    sku VARCHAR(50) UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,

    id_categoria INT 
        REFERENCES inventario.categorias(id_categoria),

    id_marca INT 
        REFERENCES inventario.marcas(id_marca),

    id_unidad INT 
        REFERENCES inventario.unidades(id_unidad),

    precio_compra  DECIMAL(12,2) 
        CHECK (precio_compra >= 0) NOT NULL,

    precio_venta DECIMAL(12,2) 
        CHECK (precio_venta >= 0) NOT NULL,

    stock_minimo INT 
        CHECK (stock_minimo >=0),

    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CREACIÓN DE LAS TABLA DE TERCER NIVEL
-- ========================================

-- CREACIÓN DE LA TABLA inventario EN EL SCHEMA inventario

CREATE TABLE inventario.inventario (
    id_producto INT PRIMARY KEY 
    REFERENCES inventario.productos(id_producto) 
    ON DELETE CASCADE,

    stock_actual INT NOT NULL CHECK (stock_actual >= 0),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- CREACIÓN DE LAS TABLAS DE TRANSACCIONALES
-- ==========================================

-- CREACIÓN DE LA TABLA compras EN EL SCHEMA compras

CREATE TABLE compras.compras (
    id_compra SERIAL PRIMARY KEY,
    id_proveedor INT NOT NULL,
    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    impuestos DECIMAL(12,2) DEFAULT 0.00,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    id_usuario INT NOT NULL,

    CONSTRAINT fk_compras_proveedor
        FOREIGN KEY (id_proveedor)
        REFERENCES compras.proveedores(id_proveedor)
        ON DELETE RESTRICT,

    CONSTRAINT fk_compras_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES seguridad.usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_estado_compras CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA'))
);

-- CREACIÓN DE LA TABLA detalle_compras EN EL SCHEMA compras

CREATE TABLE compras.detalle_compras (
    id_detalle SERIAL PRIMARY KEY,
    id_compra INT REFERENCES compras.compras(id_compra) ON DELETE CASCADE,
    id_producto INT REFERENCES inventario.productos(id_producto) ON DELETE RESTRICT,
    cantidad INT NOT NULL,
    costo_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL
);

-- CREACIÓN DE LA TABLA ventas EN EL SCHEMA ventas

CREATE TABLE ventas.ventas (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES ventas.clientes(id_cliente) ON DELETE RESTRICT,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    impuestos NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    descuento NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    total NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    id_usuario INT REFERENCES seguridad.usuarios(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT chk_estado_ventas CHECK (estado IN ('PENDIENTE', 'COMPLETADA', 'ANULADA'))
);

CREATE TABLE ventas.detalle_venta ( 
    id_detalle SERIAL PRIMARY KEY,
    id_venta INT REFERENCES ventas.ventas(id_venta) ON DELETE CASCADE,
    id_producto INT REFERENCES inventario.productos(id_producto) ON DELETE RESTRICT,
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL
);

CREATE TABLE inventario.movimientos_inventario (
    id_movimiento SERIAL PRIMARY KEY,
    id_producto INT REFERENCES inventario.productos(id_producto) ON DELETE RESTRICT,
    tipo_movimiento VARCHAR(20) NOT NULL 
        CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION')),
    cantidad INT NOT NULL,
    referencia VARCHAR(100),
    observacion TEXT,
    id_usuario INT REFERENCES seguridad.usuarios(id_usuario) ON DELETE RESTRICT,
    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- AUDITORÍA EN LA TABLA PRODUCTOS
-- ===============================

-- CREACIÓN FUNCIÓN

CREATE OR REPLACE FUNCTION actualizar_fecha_mod_productos()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_modificacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- CREACIÓN TRIGGER

CREATE TRIGGER tg_actualizar_productos
BEFORE UPDATE ON inventario.productos
FOR EACH ROW
EXECUTE FUNCTION actualizar_fecha_mod_productos();
