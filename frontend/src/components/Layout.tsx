/*
 * ============================================================================
 * Layout.tsx  ·  Estructura (marco) de la aplicación autenticada
 * ============================================================================
 * ¿Qué es?
 *   El componente que envuelve TODAS las páginas internas de la app una vez
 *   que el usuario inició sesión. Pinta la barra lateral de navegación, la
 *   barra superior para móvil y el área donde se muestra la página actual.
 *
 * ¿Para qué sirve?
 *   - Mostrar el menú de secciones (Dashboard, Punto de venta, Pizarra, etc.).
 *   - Ocultar opciones avanzadas (Insumos, Costeo, Reportes, Usuarios,
 *     Configuración) a los usuarios que no son administradores.
 *   - Mostrar en tiempo real un "badge" (número) con las notas pendientes de
 *     la Pizarra, actualizándose vía Server-Sent Events (SSE).
 *   - Cerrar la sesión del usuario.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - En `App.tsx` se usa como elemento de la ruta "padre": envuelve a todas las
 *     páginas hijas. El contenido de cada página hija se inyecta donde está
 *     `<Outlet />`.
 *   - `useAuth` (de `../auth`) da el usuario actual y el `logout`.
 *   - `useConfig` (de `../config`) da el logo configurable.
 *   - `api`, `eventSourceUrl` y `getToken` (de `../api`) se usan para consultar
 *     el backend y abrir el canal de eventos en vivo.
 * ============================================================================
 */

// Hooks de React: useEffect (efectos secundarios) y useState (estado local).
import { useEffect, useState } from "react";
// NavLink: enlace con estado "activo". Outlet: hueco donde se pinta la página hija.
// useLocation: nos dice en qué ruta estamos para cerrar el menú móvil al navegar.
import { NavLink, Outlet, useLocation } from "react-router-dom";
// api: helper para llamar al backend. eventSourceUrl/getToken: para el canal SSE.
import { api, eventSourceUrl, getToken } from "../api";
// useAuth: usuario logueado y acción de cerrar sesión.
import { useAuth } from "../auth";
// useConfig: logo configurable del negocio.
import { useConfig } from "../config";

// Tipo que describe cada elemento del menú lateral.
interface NavItem {
  to: string; // Ruta a la que navega el enlace (ej: "/productos").
  label: string; // Texto visible (ej: "Productos").
  icon: string; // Nombre del ícono (Material Symbols).
  end?: boolean; // Si es true, el enlace solo se marca activo en coincidencia exacta.
}

export default function Layout() {
  // Usuario actual y función para cerrar sesión, desde el contexto de auth.
  const { user, logout } = useAuth();
  // Logo configurable del negocio, desde el contexto de configuración.
  const { logo } = useConfig();
  // Información de la ubicación/ruta actual de la app.
  const location = useLocation();
  // Controla si el menú lateral está abierto en pantallas pequeñas (móvil).
  const [abierto, setAbierto] = useState(false);
  // Cantidad de notas pendientes de la Pizarra (se muestra como badge rojo).
  const [pendientes, setPendientes] = useState(0);

  // Cada vez que cambia la ruta, cerramos el menú móvil automáticamente.
  useEffect(() => {
    setAbierto(false);
  }, [location.pathname]);

  // Efecto que trae las notas pendientes y las mantiene actualizadas en vivo.
  useEffect(() => {
    // Función interna que consulta al backend el resumen de la pizarra.
    const refrescar = () =>
      api<{ pendientes: number }>("/notas/resumen")
        .then((r) => setPendientes(r.pendientes)) // guardamos el número recibido
        .catch(() => {}); // si falla, no rompemos la pantalla (silencioso)
    refrescar(); // Primera carga al montar el componente.
    // Abrimos un canal de eventos en tiempo real (SSE) con el backend.
    // El token va en la URL porque EventSource no admite cabeceras.
    const es = new EventSource(
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    // Cada vez que llega un mensaje desde el servidor...
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as { type: string };
      // Si el evento está relacionado con notas, volvemos a pedir el resumen.
      if (msg.type.startsWith("nota_")) refrescar();
    };
    // Función de limpieza: al desmontar el componente cerramos el canal SSE
    // para no dejar conexiones abiertas.
    return () => es.close();
  }, []);

  // Lista base de enlaces del menú, visible para todos los usuarios.
  const links: NavItem[] = [
    { to: "/", label: "Dashboard", icon: "space_dashboard", end: true },
    { to: "/pos", label: "Punto de venta", icon: "point_of_sale" },
    { to: "/pizarra", label: "Pizarra", icon: "sticky_note_2" },
    { to: "/productos", label: "Productos", icon: "inventory_2" },
    { to: "/ventas", label: "Ventas", icon: "receipt_long" },
    { to: "/proveedores", label: "Proveedores", icon: "local_shipping" },
    { to: "/compras", label: "Compras", icon: "shopping_cart" },
  ];
  // Si el usuario es administrador, agregamos las secciones avanzadas.
  if (user?.rol === "admin") {
    links.push({ to: "/insumos", label: "Insumos", icon: "grocery" });
    links.push({ to: "/costeo", label: "Costeo", icon: "calculate" });
    links.push({ to: "/reportes", label: "Reportes", icon: "monitoring" });
    links.push({ to: "/usuarios", label: "Usuarios", icon: "group" });
    links.push({ to: "/configuracion", label: "Configuración", icon: "settings" });
  }

  // --- Marcado (JSX) del layout ---
  return (
    <div className="app">
      {/* Barra lateral (menú de navegación). La clase "open" la muestra en móvil. */}
      <aside className={abierto ? "sidebar open" : "sidebar"}>
        {/* Cabecera de la barra lateral: logo + nombre + etiqueta "POS". */}
        <div className="sidebar-brand">
          {/* Si hay logo lo mostramos; si no, un recuadro con la letra "B". */}
          {logo ? (
            <img className="logo" src={logo} alt="Logo" />
          ) : (
            <span className="logo-placeholder">B</span>
          )}
          <span className="brand-name">Cafetería POS</span>
          <span className="brand-badge">POS</span>
        </div>

        {/* Menú de enlaces: recorremos el arreglo `links` con .map(). */}
        <nav className="sidebar-nav">
          {links.map((l) => (
            // NavLink aplica la clase "active" cuando la ruta coincide.
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                isActive ? "nav-item active" : "nav-item"
              }
            >
              {/* Ícono (Material Symbols) y texto del enlace. */}
              <span className="material-symbols-outlined">{l.icon}</span>
              {l.label}
              {/* En el enlace de Pizarra mostramos el badge con las pendientes,
                  pero solo si hay al menos una. */}
              {l.to === "/pizarra" && pendientes > 0 && (
                <span className="nav-badge">{pendientes}</span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Pie de la barra lateral: nombre del usuario y botón de salir. */}
        <div className="sidebar-footer">
          <span className="user-name">{user?.nombre}</span>
          <button className="ghost" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Fondo oscuro que aparece en móvil cuando el menú está abierto.
          Al hacer clic sobre él se cierra el menú. */}
      {abierto && <div className="backdrop" onClick={() => setAbierto(false)} />}

      {/* Área principal donde se muestra la página actual. */}
      <main className="main">
        {/* Barra superior, pensada para pantallas pequeñas (móvil). */}
        <header className="topbar-mobile">
          {/* Botón "hamburguesa" que abre el menú lateral. */}
          <button
            className="icon-btn"
            aria-label="Abrir menú"
            onClick={() => setAbierto(true)}
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
          {/* Título de la barra superior: logo (o "B") + nombre + "POS". */}
          <span className="topbar-title">
            {logo ? (
              <img className="logo" src={logo} alt="Logo" />
            ) : (
              <span className="logo-placeholder">B</span>
            )}
            Cafetería POS
            <span className="brand-badge">POS</span>
          </span>
          {/* Nombre del usuario: mostramos solo la primera palabra (nombre). */}
          <span className="topbar-user">{user?.nombre?.split(" ")[0]}</span>
        </header>

        {/* Contenedor de la página. La `key` cambia al navegar para forzar
            que el contenido se vuelva a montar (limpia estado de la página). */}
        <div className="page" key={location.pathname}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
