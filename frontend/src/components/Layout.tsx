import { NavLink, Outlet, useLocation } from "react-router-dom";
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

  const links: NavItem[] = [
    { to: "/", label: "Dashboard", icon: "space_dashboard", end: true },
    { to: "/pos", label: "Punto de venta", icon: "point_of_sale" },
    { to: "/productos", label: "Productos", icon: "inventory_2" },
    { to: "/ventas", label: "Ventas", icon: "receipt_long" },
    { to: "/proveedores", label: "Proveedores", icon: "local_shipping" },
    { to: "/compras", label: "Compras", icon: "shopping_cart" },
    { to: "/reportes", label: "Reportes", icon: "monitoring" },
  ];
  if (user?.rol === "admin") {
    links.push({ to: "/usuarios", label: "Usuarios", icon: "group" });
    links.push({ to: "/configuracion", label: "Configuración", icon: "settings" });
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          {logo ? (
            <img className="logo" src={logo} alt="Logo" />
          ) : (
            <span className="logo-placeholder">B</span>
          )}
          <span className="brand-name">Cafetería POS</span>
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

      <main className="main">
        <div className="page" key={location.pathname}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
