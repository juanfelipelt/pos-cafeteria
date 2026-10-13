"""Repositorios del dominio: los "puertos" de la aplicación.

Un repositorio es una *interfaz*: una lista de métodos (get, list, add...)
que describen **qué** se puede hacer con las entidades, pero no **cómo** se
hace. Por ejemplo, ``ProductoRepository`` dice "existe una forma de obtener un
producto por su id", sin importar si los datos están en PostgreSQL, en Excel o
en memoria.

Esta separación es la base de la arquitectura por capas (puertos y
adaptadores): la capa de dominio y de aplicación solo conocen estas interfaces,
y la infraestructura se encarga de implementarlas de verdad.
"""
