/*
 * auth.tsx — Manejo de la autenticación (inicio/cierre de sesión) en la app.
 *
 * ¿Qué es? Un "contexto" de React que guarda quién es el usuario logueado y
 * ofrece funciones para iniciar y cerrar sesión.
 *
 * ¿Para qué sirve?
 *   - Recordar el usuario actual (o null si nadie ha iniciado sesión).
 *   - Saber si la app todavía está "cargando" (loading) mientras verifica el
 *     token guardado.
 *   - Iniciar sesión (login) contra el backend y guardar el token JWT.
 *   - Cerrar sesión (logout) borrando el token.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   App.tsx envuelve todo con <AuthProvider>. Cualquier componente puede leer
 *   el estado con el hook useAuth(). El componente Protected.tsx lo usa para
 *   decidir si permite ver una página o redirige a /login. La comunicación
 *   con el backend se hace con la función api() de ./api.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, clearToken, getToken, setToken } from "./api";

// Representa a un usuario autenticado tal como lo devuelve el backend.
export interface User {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  estado: boolean;
}

// Forma (contrato) del valor que compartirá el contexto de autenticación.
interface AuthContextValue {
  user: User | null; // Usuario actual, o null si no hay sesión.
  loading: boolean; // true mientras se verifica si hay sesión activa.
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// Se crea el contexto vacío. El valor inicial es null; los componentes deben
// consumirlo dentro del <AuthProvider> (si no, useAuth lanzará un error).
const AuthContext = createContext<AuthContextValue | null>(null);

// Provider: componente que envuelve la app y expone el estado de auth.
export function AuthProvider({ children }: { children: ReactNode }) {
  // Estado con el usuario logueado. Empieza como null (nadie logueado).
  const [user, setUser] = useState<User | null>(null);

  // Estado de "cargando". Arranca en true SOLO si ya existía un token en
  // localStorage (hay que validarlo). Si no hay token, arranca en false.
  const [loading, setLoading] = useState<boolean>(() => Boolean(getToken()));

  // Efecto que se ejecuta UNA vez al montar el provider: si hay token guardado,
  // preguntamos al backend por el usuario actual ("/auth/me"). Si el token es
  // válido guardamos el usuario; si falla, borramos el token. Al terminar,
  // apagamos el estado de carga.
  useEffect(() => {
    if (getToken()) {
      api<User>("/auth/me")
        .then(setUser) // Guardamos el usuario devuelto por el backend.
        .catch(() => clearToken()) // Token inválido: lo eliminamos.
        .finally(() => setLoading(false)); // Terminó la verificación.
    } else {
      setLoading(false); // No había token: no hay nada que verificar.
    }
  }, []); // Arreglo vacío = se ejecuta solo una vez.

  // login: envía email y contraseña al backend; si todo va bien, guarda el
  // token JWT y actualiza el usuario en memoria.
  async function login(email: string, password: string) {
    const data = await api<{ access_token: string; usuario: User }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
    setToken(data.access_token); // Guardamos el token para futuras peticiones.
    setUser(data.usuario); // Guardamos los datos del usuario.
  }

  // logout: borra el token y limpia el usuario (vuelve a estado sin sesión).
  function logout() {
    clearToken();
    setUser(null);
  }

  // Publicamos el estado y las funciones para que los consumidores las usen.
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook personalizado para consumir el contexto desde cualquier componente.
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  // Protección: si se usa fuera del provider, avisamos con un error claro.
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
