/*
 * components/Protected.tsx — Guardián de rutas privadas.
 *
 * ¿Qué es? Un componente "envoltorio" que decide si se puede mostrar una
 * página o si hay que mandar al usuario a iniciar sesión.
 *
 * ¿Para qué sirve?
 *   - Mientras la app verifica la sesión (loading), muestra "Cargando…".
 *   - Si NO hay usuario autenticado, redirige a /login.
 *   - Si SÍ hay usuario, muestra el contenido (children).
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   App.tsx envuelve el <Layout /> y todas las rutas privadas con
 *   <Protected>. Usa el hook useAuth() de auth.tsx y el componente Navigate
 *   de react-router-dom para hacer la redirección.
 */

import { Navigate } from "react-router-dom";
import { useAuth } from "../auth";
import type { ReactNode } from "react";

// children: el contenido que se mostrará solo si el usuario está autenticado.
export default function Protected({ children }: { children: ReactNode }) {
  // Leemos del contexto de auth si hay usuario y si aún estamos cargando.
  const { user, loading } = useAuth();

  // Mientras se comprueba la sesión, evitamos mostrar la página protegida
  // (y evitar redirecciones equivocadas) mostrando una pantalla de carga.
  if (loading) {
    return <div className="loading-screen">Cargando…</div>;
  }

  // Sin usuario: redirigimos al login. "replace" reemplaza la ruta actual en
  // el historial para que el botón "atrás" no vuelva a la página protegida.
  if (!user) return <Navigate to="/login" replace />;

  // Con usuario: renderizamos el contenido solicitado.
  return <>{children}</>;
}
