<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cafetería POS | Producto</title>
    <link rel="stylesheet" href="${pageContext.request.contextPath}/css/estilos.css">
</head>
<body>
<header class="cabecera">
    <h1>Cafetería POS <span>· Módulo de productos</span></h1>
    <a class="boton secundario" href="${pageContext.request.contextPath}/productos">← Volver al listado</a>
</header>

<main class="contenedor">
    <h2>
        <c:choose>
            <c:when test="${empty producto.id}">Registrar producto</c:when>
            <c:otherwise>Editar producto</c:otherwise>
        </c:choose>
    </h2>

    <!-- Formulario HTML que envia los datos por POST al servlet de productos -->
    <form class="formulario" action="${pageContext.request.contextPath}/productos" method="post">
        <input type="hidden" name="accion" value="guardar">
        <input type="hidden" name="id" value="${producto.id}">

        <label>
            Nombre del producto
            <input type="text" name="nombre" value="<c:out value='${producto.nombre}'/>" required maxlength="120">
        </label>

        <label>
            Categoría
            <input type="text" name="categoria" value="<c:out value='${producto.categoria}'/>" maxlength="80">
        </label>

        <label>
            Precio
            <input type="number" name="precio" value="${producto.precio}" min="0" step="50" required>
        </label>

        <label class="check">
            <input type="checkbox" name="activo" <c:if test="${producto.activo}">checked</c:if>>
            Producto activo para la venta
        </label>

        <div class="botones">
            <button type="submit" class="boton">Guardar</button>
            <a class="boton secundario" href="${pageContext.request.contextPath}/productos">Cancelar</a>
        </div>
    </form>
</main>
</body>
</html>
