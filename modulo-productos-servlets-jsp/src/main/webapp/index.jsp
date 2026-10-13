<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%-- Página de bienvenida: redirige al módulo de productos --%>
<% response.sendRedirect(request.getContextPath() + "/productos"); %>
