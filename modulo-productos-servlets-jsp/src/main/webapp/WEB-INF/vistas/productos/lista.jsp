<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cafetería POS | Productos</title>
    <link rel="stylesheet" href="${pageContext.request.contextPath}/css/estilos.css">
</head>
<body>
<header class="cabecera">
    <h1>Cafetería POS <span>· Módulo de productos</span></h1>
    <a class="boton" href="${pageContext.request.contextPath}/productos?accion=nuevo">+ Nuevo producto</a>
</header>

<main class="contenedor">
    <c:choose>
        <c:when test="${empty productos}">
            <p class="vacio">Todavía no hay productos registrados. Crea el primero con el botón “Nuevo producto”.</p>
        </c:when>
        <c:otherwise>
            <table class="tabla">
                <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Categoría</th>
                    <th>Precio</th>
                    <th>Activo</th>
                    <th>Acciones</th>
                </tr>
                </thead>
                <tbody>
                <c:forEach var="producto" items="${productos}">
                    <tr>
                        <td>${producto.id}</td>
                        <td><c:out value="${producto.nombre}"/></td>
                        <td><c:out value="${producto.categoria}"/></td>
                        <td>$<fmt:formatNumber value="${producto.precio}" minFractionDigits="0" maxFractionDigits="0"/></td>
                        <td>
                            <c:choose>
                                <c:when test="${producto.activo}">
                                    <span class="etiqueta activo">Sí</span>
                                </c:when>
                                <c:otherwise>
                                    <span class="etiqueta inactivo">No</span>
                                </c:otherwise>
                            </c:choose>
                        </td>
                        <td class="acciones">
                            <a href="${pageContext.request.contextPath}/productos?accion=editar&id=${producto.id}">Editar</a>
                            <a class="eliminar"
                               href="${pageContext.request.contextPath}/productos?accion=eliminar&id=${producto.id}"
                               onclick="return confirm('¿Seguro que deseas eliminar este producto?');">Eliminar</a>
                        </td>
                    </tr>
                </c:forEach>
                </tbody>
            </table>
        </c:otherwise>
    </c:choose>
</main>
</body>
</html>
