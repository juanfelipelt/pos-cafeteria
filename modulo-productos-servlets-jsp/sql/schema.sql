-- Esquema de la base de datos del módulo de productos de Cafetería POS.
-- Base de datos: SQLite (archivo pos-cafeteria.db). El servlet crea esta tabla automáticamente
-- al iniciar, pero se deja el script para su documentación y despliegue manual.

CREATE TABLE IF NOT EXISTS producto (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL,
    categoria TEXT,
    precio    REAL    NOT NULL,
    activo    INTEGER NOT NULL DEFAULT 1
);

-- Datos de ejemplo (opcional)
INSERT INTO producto (nombre, categoria, precio, activo) VALUES
    ('Capuchino',            'Bebidas',  5500,  1),
    ('Café americano',       'Bebidas',  4000,  1),
    ('Croissant de jamón',   'Panadería',7500,  1),
    ('Porción de torta',     'Postres',  8000,  1),
    ('Jugo natural',         'Bebidas',  6000,  0);
