/*
 * App.tsx — Componente raíz de la aplicación Cafetería POS.
 *
 * ¿Qué es? El componente principal que organiza toda la app: envuelve la
 * aplicación con los "providers" (proveedores de datos globales) y define
 * las rutas (URLs) que llevan a cada pantalla.
 *
 * ¿Para qué sirve?
 *   - AuthProvider: guarda la sesión del usuario (quién está logueado).
 *   - ConfigProvider: guarda la configuración global (por ejemplo el logo).
 *   - BrowserRouter: permite navegar entre páginas cambiando la URL sin
 *     recargar el navegador.
 *   - Routes/Route: mapean cada dirección URL con el componente de página
 *     que se debe mostrar.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   main.tsx monta <App />. Aquí se decide qué pantalla se ve según la URL:
 *   /login (público) y el resto protegidas por <Protected>, que solo deja
 *   pasar si hay un usuario autenticado.
 */

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth";
import { ConfigProvider } from "./config";
import Protected from "./components/Protected";
import Layout from "./components/Layout";
// Páginas (cada una es una pantalla completa de la app).
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import POS from "./pages/POS";
import Pizarra from "./pages/Pizarra";
import Productos from "./pages/Productos";
import Ventas from "./pages/Ventas";
import Proveedores from "./pages/Proveedores";
import Compras from "./pages/Compras";
import Insumos from "./pages/Insumos";
import Costeo from "./pages/Costeo";
import Reportes from "./pages/Reportes";
import Configuracion from "./pages/Configuracion";
import Usuarios from "./pages/Usuarios";

export default function App() {
  return (
    /* AuthProvider: provee el estado de autenticación a TODOS los
       componentes hijos (se consulta con el hook useAuth()). */
    <AuthProvider>
      {/* ConfigProvider: provee la configuración global (logo, etc.). */}
      <ConfigProvider>
        {/* BrowserRouter: maneja la navegación por URL sin recargar. */}
        <BrowserRouter>
          <Routes>
            {/* Ruta pública: la pantalla de inicio de sesión. No requiere
                estar autenticado para poder verla. */}
            <Route path="/login" element={<Login />} />

            {/* Ruta "padre" sin path que envuelve al resto: solo se muestra
                si <Protected> permite el acceso y usa <Layout> como marco
                (sidebar + área principal). Las rutas hijas se dibujan donde
                el Layout coloque su <Outlet />. */}
            <Route
              element={
                <Protected>
                  <Layout />
                </Protected>
              }
            >
              {/* Cada ruta hija corresponde a una sección del menú. */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/pos" element={<POS />} />
              <Route path="/pizarra" element={<Pizarra />} />
              <Route path="/productos" element={<Productos />} />
              <Route path="/ventas" element={<Ventas />} />
              <Route path="/proveedores" element={<Proveedores />} />
              <Route path="/compras" element={<Compras />} />
              <Route path="/insumos" element={<Insumos />} />
              <Route path="/costeo" element={<Costeo />} />
              <Route path="/reportes" element={<Reportes />} />
              <Route path="/configuracion" element={<Configuracion />} />
              <Route path="/usuarios" element={<Usuarios />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </AuthProvider>
  );
}
