# Documentación de los servicios web — Proyecto Cafetería POS

**Evidencia:** GA7-220501096-AA5-EV03 — Diseño y desarrollo de servicios web (proyecto)

**Proyecto:** Cafetería POS — MiniPOS para una cafetería

**Aprendiz:** Juan Felipe López Tobón

**Programa:** Tecnología en Análisis y Desarrollo de Software — SENA


## 1. Introducción

Este documento describe cada uno de los servicios web (API REST) que conforman el proyecto Cafetería POS. La API fue construida con **FastAPI (Python)**, sigue el patrón REST y se organiza en routers por dominio funcional. Se documentan los métodos, las rutas y el nivel de autenticación requerido por cada servicio.

La API cuenta con **13 servicios** y **58 endpoints** en total.

## 2. Convenciones generales

- **URL base:** `/` (por ejemplo, `http://localhost:8000`).
- **Autenticación:** token **JWT** enviado en la cabecera `Authorization: Bearer <token>`.
- **Formato:** peticiones y respuestas en **JSON** (UTF-8).
- **Códigos:** `200/201` éxito, `400` datos inválidos, `401` no autenticado, `403` sin permisos, `404` no encontrado, `409` conflicto.

## 3. Resumen de servicios

| # | Servicio | Descripción | Prefijo | Endpoints |
|---|----------|-------------|---------|-----------|
| 1 | `auth` | Autenticación y usuarios | `/auth` | 4 |
| 2 | `categorias` | Categorías de productos | `/categorias` | 4 |
| 3 | `compras` | Compras a proveedores | `/compras` | 6 |
| 4 | `configuracion` | Configuración del negocio | `/configuracion` | 3 |
| 5 | `costeo` | Costeo de productos | `/costeo` | 2 |
| 6 | `costos_fijos` | Costos fijos | `/costos-fijos` | 5 |
| 7 | `eventos` | Eventos en tiempo real (SSE) | `/eventos` | 0 |
| 8 | `insumos` | Insumos y materias primas | `/insumos` | 6 |
| 9 | `notas` | Notas y gastos | `/notas` | 5 |
| 10 | `productos` | Productos | `/productos` | 7 |
| 11 | `proveedores` | Proveedores | `/proveedores` | 6 |
| 12 | `reportes` | Reportes | `/reportes` | 4 |
| 13 | `ventas` | Ventas (POS) | `/ventas` | 6 |

## 4. Detalle de cada servicio

### 4.1 Autenticación y usuarios (`auth`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| POST | `/auth/login` | Iniciar sesión | Pública |
| POST | `/auth/registro` | Registrar | Bearer · Administrador |
| GET | `/auth/me` | Consultar el usuario autenticado | Bearer · Usuario |
| GET | `/auth/usuarios` | listar_usuarios | Bearer · Administrador |

### 4.2 Categorías de productos (`categorias`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/categorias` | Listar registros | Pública |
| POST | `/categorias` | Crear registro | Pública |
| GET | `/categorias/{categoria_id}` | Consultar un registro por id | Pública |
| PUT | `/categorias/{categoria_id}` | Actualizar un registro | Pública |

### 4.3 Compras a proveedores (`compras`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| POST | `/compras` | Crear registro | Pública |
| GET | `/compras` | Listar registros | Pública |
| GET | `/compras/{compra_id}` | Consultar un registro por id | Pública |
| PUT | `/compras/{compra_id}` | Actualizar un registro | Bearer · Administrador |
| POST | `/compras/{compra_id}/anular` | Anular el registro | Bearer · Administrador |
| DELETE | `/compras/{compra_id}` | Eliminar un registro | Bearer · Administrador |

### 4.4 Configuración del negocio (`configuracion`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/configuracion` | obtener_todas | Pública |
| PUT | `/configuracion/logo` | establecer_logo | Bearer · Administrador |
| PUT | `/configuracion/{clave}` | establecer_valor | Bearer · Administrador |

### 4.5 Costeo de productos (`costeo`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/costeo/productos` | productos | Pública |
| GET | `/costeo/resumen` | Obtener el resumen | Pública |

### 4.6 Costos fijos (`costos_fijos`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/costos-fijos` | Listar registros | Pública |
| POST | `/costos-fijos` | Crear registro | Bearer · Administrador |
| GET | `/costos-fijos/{costo_id}` | Consultar un registro por id | Pública |
| PUT | `/costos-fijos/{costo_id}` | Actualizar un registro | Bearer · Administrador |
| DELETE | `/costos-fijos/{costo_id}` | Eliminar un registro | Bearer · Administrador |

### 4.7 Eventos en tiempo real (SSE) (`eventos`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|

### 4.8 Insumos y materias primas (`insumos`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/insumos` | Listar registros | Pública |
| POST | `/insumos` | Crear registro | Bearer · Administrador |
| GET | `/insumos/{insumo_id}` | Consultar un registro por id | Pública |
| PUT | `/insumos/{insumo_id}` | Actualizar un registro | Bearer · Administrador |
| PATCH | `/insumos/{insumo_id}/estado` | Cambiar el estado del registro | Bearer · Administrador |
| DELETE | `/insumos/{insumo_id}` | Eliminar un registro | Bearer · Administrador |

### 4.9 Notas y gastos (`notas`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/notas` | Listar registros | Pública |
| GET | `/notas/resumen` | Obtener el resumen | Pública |
| POST | `/notas` | Crear registro | Bearer · Usuario |
| PATCH | `/notas/{nota_id}` | Actualizar un registro | Bearer · Usuario |
| DELETE | `/notas/{nota_id}` | Eliminar un registro | Bearer · Usuario |

### 4.10 Productos (`productos`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/productos` | Listar registros | Pública |
| POST | `/productos` | Crear registro | Pública |
| GET | `/productos/{producto_id}` | Consultar un registro por id | Pública |
| PUT | `/productos/{producto_id}` | Actualizar un registro | Pública |
| PATCH | `/productos/{producto_id}/estado` | Cambiar el estado del registro | Pública |
| GET | `/productos/{producto_id}/receta` | obtener_receta | Pública |
| PUT | `/productos/{producto_id}/receta` | establecer_receta | Pública |

### 4.11 Proveedores (`proveedores`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/proveedores` | Listar registros | Pública |
| POST | `/proveedores` | Crear registro | Pública |
| GET | `/proveedores/{proveedor_id}` | Consultar un registro por id | Pública |
| PUT | `/proveedores/{proveedor_id}` | Actualizar un registro | Pública |
| PATCH | `/proveedores/{proveedor_id}/estado` | Cambiar el estado del registro | Pública |
| DELETE | `/proveedores/{proveedor_id}` | Eliminar un registro | Bearer · Administrador |

### 4.12 Reportes (`reportes`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| GET | `/reportes/resumen` | Obtener el resumen | Pública |
| GET | `/reportes/ventas` | ventas_por_periodo | Pública |
| GET | `/reportes/actividad` | Reporte de actividad | Pública |
| GET | `/reportes/top-productos` | Productos más vendidos | Pública |

### 4.13 Ventas (POS) (`ventas`)

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|----------------|
| POST | `/ventas` | Crear registro | Bearer · Usuario |
| GET | `/ventas` | Listar registros | Pública |
| GET | `/ventas/{venta_id}` | Consultar un registro por id | Pública |
| POST | `/ventas/{venta_id}/pagos` | registrar_pago | Pública |
| POST | `/ventas/{venta_id}/anular` | Anular el registro | Bearer · Administrador |
| DELETE | `/ventas/{venta_id}` | Eliminar un registro | Bearer · Administrador |
