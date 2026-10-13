# Cafetería POS

Proyecto formativo del SENA para la gestión de una cafetería (punto de venta). Reúne las
evidencias de la Guía de Aprendizaje 7 (competencia **220501096** — *Desarrollar la solución
de software de acuerdo con el diseño y metodologías de desarrollo*).

**Aprendiz:** Juan Felipe López Tobón
**Programa:** Tecnología en Análisis y Desarrollo de Software (SENA)

## Nota sobre este repositorio

Este repositorio es una **copia (clon) académica** del sistema que desarrollé para mi
cafetería, el cual **ya se encuentra en producción y en funcionamiento**.

Para esta entrega del SENA se **eliminó la información sensible** (datos y decisiones del
negocio, credenciales, configuración de producción y notas privadas), dejando únicamente el
**código fuente comentado con fines educativos**. Por eso el historial de cambios es el del
proyecto real, pero sin el contenido reservado.

## Evidencias incluidas

| Evidencia | Componente | Carpeta |
|---|---|---|
| **GA7-220501096-AA2-EV02** | Módulo web con **Servlets + JSP** (formularios HTML, GET/POST, JDBC) | `modulo-productos-servlets-jsp/` |
| **GA7-220501096-AA4-EV03** | **Front-end en React** (Vite) | `frontend/` |
| **GA7-220501096-AA5-EV03** | **Servicios web / API** (FastAPI) | raíz del repo (backend) |

## Estructura

```
.
├── frontend/                       # Aplicación React (AA4-EV03)
├── modulo-productos-servlets-jsp/  # Módulo Java Servlets + JSP (AA2-EV02)
├── app.py                          # Punto de entrada de la API (AA5-EV03)
├── application/                    # Casos de uso, schemas y seguridad
├── domain/                         # Entidades y puertos (repositorios)
├── infrastructure/                 # API, modelos ORM y repositorios
├── migrations/                     # Migraciones de base de datos (Alembic)
├── tests/                          # Pruebas unitarias e integración
├── requirements.txt
└── DOCUMENTACION_SERVICIOS.md/pdf  # Documentación de la API (AA5-EV03)
```

## Tecnologías

- **Back-end / API:** Python + FastAPI, SQLAlchemy, Alembic, JWT.
- **Front-end:** React + TypeScript + Vite.
- **Módulo web:** Java + Servlets + JSP + JDBC (SQLite) con Maven.
- **Base de datos:** SQLite (desarrollo).

Todo el código está comentado para facilitar su lectura y evaluación.
