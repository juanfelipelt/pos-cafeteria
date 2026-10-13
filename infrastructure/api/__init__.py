"""
Paquete de la capa de API (interfaz HTTP) del proyecto Cafetería POS.

Aquí vive todo lo relacionado con exponer el sistema por HTTP usando FastAPI:
- `dependencies.py`: dependencias de seguridad reutilizables (autenticación y
  autorización) que usan los endpoints.
- `routers/`: los "routers" o conjuntos de endpoints agrupados por recurso
  (productos, ventas, insumos, etc.).

La idea de separar la API en un paquete es mantener ordenado el código: la
lógica de negocio vive en `application/`, las reglas del dominio en `domain/`
y el acceso a datos en `infrastructure/repositories/`. Esta capa solo se
encarga de recibir peticiones HTTP y devolver respuestas.
"""
