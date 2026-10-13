"""Entidades del dominio y enumeraciones del negocio.

Cada archivo de este paquete representa un concepto del negocio (una
categoría, un producto, una venta, un cliente...). Las entidades son
"dataclasses": objetos sencillos que guardan datos y que validan ellos mismos
sus reglas básicas dentro de ``__post_init__``, para que nunca exista en el
sistema una entidad con datos inválidos.
"""
