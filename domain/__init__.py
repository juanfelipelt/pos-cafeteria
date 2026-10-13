"""Capa de dominio del proyecto Cafetería POS.

Aquí vive el *corazón* del negocio: las reglas que no dependen de la base de
datos, del framework web ni de ningún detalle técnico. Se divide en dos:

- ``entities``: los objetos del negocio (Producto, Venta, Usuario, etc.) con
  sus datos y sus reglas de validación.
- ``repositories``: las interfaces (puertos) que describen cómo se guardan y
  se leen esas entidades, sin decir *cómo* se hace.

Mantener el dominio aislado permite reutilizar y probar las reglas del negocio
sin necesidad de levantar todo el sistema.
"""
