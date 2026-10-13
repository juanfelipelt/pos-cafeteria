# Cafetería POS · Módulo de Productos (Servlets + JSP)

Módulo web del proyecto **Cafetería POS** (MiniPOS para una cafetería) desarrollado con
**Servlets + JSP**, formularios HTML, métodos **GET/POST** y conexión a base de datos
por **JDBC**.

- **Evidencia:** GA7-220501096-AA2-EV02 — *Módulos de software codificados y probados*.
- **Competencia:** 220501096 — Desarrollar la solución de software de acuerdo con el diseño y metodologías de desarrollo.
- **Programa:** Tecnología en Análisis y Desarrollo de Software (SENA).
- **Aprendiz:** Juan Felipe López Tobón.

## Tecnologías

| Elemento | Tecnología |
|---|---|
| Lenguaje | Java 17 |
| Web | Jakarta/Java EE — Servlets + JSP (JSTL) |
| Formularios | HTML5 con método POST |
| Base de datos | SQLite (vía JDBC, driver `org.xerial:sqlite-jdbc`) |
| Empaquetado | Maven (`war`) |
| Servidor | Apache Tomcat 9 (o superior, con soporte `javax`) |

## Funcionalidades (CRUD)

El módulo permite **insercionar, consultar, actualizar y eliminar** productos:

- `GET  /productos` → lista los productos.
- `GET  /productos?accion=nuevo` → formulario para crear un producto.
- `GET  /productos?accion=editar&id=N` → formulario para editar el producto N.
- `GET  /productos?accion=eliminar&id=N` → elimina el producto N.
- `POST /productos` (`accion=guardar`) → inserta o actualiza según venga o no el `id`.

## Estructura del proyecto

```
AA2-EV02_source/
├── pom.xml
├── README.md
├── sql/
│   └── schema.sql
└── src/main/
    ├── java/co/edu/sena/cafeteriapos/
    │   ├── modelo/Producto.java              (entidad)
    │   ├── persistencia/ConexionBD.java      (conexión JDBC)
    │   ├── persistencia/ProductoDAO.java     (CRUD con JDBC)
    │   └── web/ProductoServlet.java          (servlet con doGet y doPost)
    └── webapp/
        ├── index.jsp
        ├── css/estilos.css
        └── WEB-INF/
            ├── web.xml
            └── vistas/productos/
                ├── lista.jsp
                └── formulario.jsp
```

## Cómo compilar y ejecutar

1. Requisitos: **JDK 17+**, **Maven** y **Apache Tomcat 9**.
2. Compilar el `war`:

   ```bash
   mvn clean package
   ```

3. Copiar el archivo `target/pos-cafeteria-productos.war` a la carpeta `webapps/` de Tomcat.
4. Iniciar Tomcat y abrir en el navegador:

   ```
   http://localhost:8080/pos-cafeteria-productos/
   ```

## Estándares de codificación aplicados

- **Clases:** `PascalCase` (por ejemplo, `ProductoDAO`, `ProductoServlet`).
- **Métodos y variables:** `camelCase` (por ejemplo, `buscarPorId`, `productoDAO`).
- **Paquetes:** minúsculas y dominio invertido (`co.edu.sena.cafeteriapos.*`).
- **Constantes:** `MAYÚSCULAS_CON_GUIONES`.
- **Comentarios:** Javadoc en clases y métodos.
