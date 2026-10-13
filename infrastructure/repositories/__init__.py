"""Repositorios concretos (implementaciones) de la capa de infraestructura.

Cada archivo de este paquete implementa un "puerto" (interfaz) definido en el
dominio (`domain.repositories.*`) usando SQLAlchemy como tecnología de
persistencia. En otras palabras: el dominio dice QUÉ operaciones necesita, y
aquí se escribe CÓMO se hacen contra la base de datos.

Patrón común de cada repositorio:
- Recibe una `Session` de SQLAlchemy (la unidad de trabajo con la BD).
- Convierte filas (modelos ORM) a entidades del dominio y viceversa.
- Usa `flush()` para enviar los cambios a la BD sin cerrar la transacción.
"""
