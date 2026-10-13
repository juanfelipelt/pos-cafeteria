"""
Routers (controladores HTTP) del proyecto Cafetería POS.

Cada archivo de este paquete define un `APIRouter` de FastAPI que agrupa los
endpoints de UN recurso del sistema. Por ejemplo:
- `auth.py`: inicio de sesión, registro y usuarios.
- `productos.py`: catálogo de productos y sus recetas.
- `ventas.py`: registro y consulta de ventas.
- `compras.py`: compras a proveedores.
- `insumos.py`, `proveedores.py`, `categorias.py`, `costos_fijos.py`,
  `configuracion.py`, `notas.py`, `reportes.py`, `costeo.py` y `eventos.py`.

Cada router se monta luego en la aplicación principal (app.py) con un prefijo
de URL, de modo que los endpoints quedan accesibles bajo rutas como
`/productos`, `/ventas`, `/insumos`, etc.
"""
