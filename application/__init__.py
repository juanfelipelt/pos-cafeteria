"""Paquete ``application`` de Cafetería POS.

Agrupa la **lógica de aplicación** (casos de uso) que queda entre la capa de
dominio (entidades y reglas de negocio puras) y la capa de infraestructura (API,
base de datos). Aquí viven utilidades y servicios de apoyo como:

- ``utils.py``: utilidades generales (por ejemplo, generar identificadores).
- ``events.py``: bus de eventos en memoria para notificaciones en tiempo real (SSE).
- ``costos.py``: cálculos de costos de productos (incluyendo combos y recetas).

Este ``__init__.py`` no contiene código; solo marca el directorio como un paquete
de Python para poder importar sus módulos (``from application.utils import ...``).
"""
