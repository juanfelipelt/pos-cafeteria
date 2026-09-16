import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api, eventSourceUrl, getToken } from "../api";
import { useAuth } from "../auth";
import { useConfig } from "../config";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
}

export default function Layout() {
  const { user, logout } = useAuth();
  const { logo } = useConfig();
  const location = useLocation();
  const [abierto, setAbierto] = useState(false);
  const [pendientes, setPendientes] = useState(0);

  useEffect(() => {
    setAbierto(false);
  }, [location.pathname]);

  useEffect(() => {
    const refrescar = () =>
      api<{ pendientes: number }>("/notas/resumen")
        .then((r) => setPendientes(r.pendientes))
        .catch(() => {});
    refrescar();
    const es = new EventSource(
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as { type: string };
      if (msg.type.startsWith("nota_")) refrescar();
    };
    return () => es.close();
  }, []);

  const links: NavItem[] = [
    { to: "/", label: "Dashboard", icon: "space_dashboard", end: true },
    { to: "/pos", label: "Punto de venta", icon: "point_of_sale" },
    { to: "/pizarra", label: "Pizarra", icon: "sticky_note_2" },
    { to: "/productos", label: "Productos", icon: "inventory_2" },
    { to: "/ventas", label: "Ventas", icon: "receipt_long" },
    { to: "/proveedores", label: "Proveedores", icon: "local_shipping" },
    { to: "/compras", label: "Compras", icon: "shopping_cart" },
  ];
  if (user?.rol === "admin") {
    links.push({ to: "/insumos", label: "Insumos", icon: "grocery" });
    links.push({ to: "/costeo", label: "Costeo", icon: "calculate" });
    links.push({ to: "/reportes", label: "Reportes", icon: "monitoring" });
    links.push({ to: "/usuarios", label: "Usuarios", icon: "group" });
    links.push({ to: "/configuracion", label: "Configuración", icon: "settings" });
  }

  return (
    <div className="app">
      <aside className={abierto ? "sidebar open" : "sidebar"}>
        <div className="sidebar-brand">
          {logo ? (
            <img className="logo" src={logo} alt="Logo" />
          ) : (
            <span className="logo-placeholder">B</span>
          )}
          <span className="brand-name">Cafetería POS</span>
          <span className="brand-badge">POS</span>
        </div>

        <nav className="sidebar-nav">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                isActive ? "nav-item active" : "nav-item"
              }
            >
              <span className="material-symbols-outlined">{l.icon}</span>
              {l.label}
              {l.to === "/pizarra" && pendientes > 0 && (
                <span className="nav-badge">{pendientes}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="user-name">{user?.nombre}</span>
          <button className="ghost" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      {abierto && <div className="backdrop" onClick={() => setAbierto(false)} />}

      <main className="main">
        <header className="topbar-mobile">
          <button
            className="icon-btn"
            aria-label="Abrir menú"
            onClick={() => setAbierto(true)}
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
          <span className="topbar-title">
            {logo ? (
              <img className="logo" src={logo} alt="Logo" />
            ) : (
              <span className="logo-placeholder">B</span>
            )}
            Cafetería POS
            <span className="brand-badge">POS</span>
          </span>
          <span className="topbar-user">{user?.nombre?.split(" ")[0]}</span>
        </header>

        <div className="page" key={location.pathname}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
