/*
 * ============================================================================
 * Login.tsx  ·  Página de inicio de sesión
 * ============================================================================
 * ¿Qué es?
 *   La pantalla pública que ve un usuario cuando aún NO ha iniciado sesión.
 *
 * ¿Para qué sirve?
 *   Muestra un formulario con Email y Contraseña. Cuando el usuario lo envía,
 *   se llama a la función `login` del contexto de autenticación (`../auth`),
 *   que a su vez consulta el backend y guarda el token. Si el login es
 *   correcto se navega al Dashboard ("/"); si falla, se muestra el error.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - En `App.tsx` está declarada como la ruta pública "/login".
 *   - Usa `useAuth` (de `../auth`) para el método `login`.
 *   - Usa `useConfig` (de `../config`) para mostrar el logo configurable.
 *   - El logo se sirve desde la configuración (ver `../../backend`, endpoint
 *     "/configuracion"); si no hay logo se muestra un texto "B" de respaldo.
 * ============================================================================
 */

// useState: hook de React para guardar datos que cambian y re-renderizan la pantalla.
import { useState } from "react";
// useNavigate: hook de react-router que permite redirigir al usuario a otra ruta por código.
import { useNavigate } from "react-router-dom";
// useAuth: contexto global que expone el método `login` y los datos del usuario.
import { useAuth } from "../auth";
// useConfig: contexto global que expone el logo configurable del negocio.
import { useConfig } from "../config";

// Componente principal de la página. Es un "componente funcional" de React.
export default function Login() {
  // Sacamos la función `login` del contexto de autenticación.
  const { login } = useAuth();
  // Sacamos el logo del contexto de configuración (puede ser null si no hay).
  const { logo } = useConfig();
  // `navigate` nos permite cambiar de pantalla luego de iniciar sesión.
  const navigate = useNavigate();
  // --- Estados locales del formulario ---
  // Correo escrito por el usuario.
  const [email, setEmail] = useState("");
  // Contraseña escrita por el usuario.
  const [password, setPassword] = useState("");
  // Mensaje de error a mostrar cuando el login falla (vacío = sin error).
  const [error, setError] = useState("");

  // Se ejecuta cuando el usuario envía el formulario (submit).
  async function handleSubmit(e: React.FormEvent) {
    // Evitamos que el navegador recargue la página (comportamiento por defecto
    // de un formulario HTML); nosotros manejamos el envío con JavaScript.
    e.preventDefault();
    // Limpiamos cualquier error anterior antes de intentar de nuevo.
    setError("");
    try {
      // Pedimos al backend iniciar sesión. `login` guarda el token si sale bien.
      await login(email, password);
      // Si no hubo error, llevamos al usuario al Dashboard (ruta raíz "/").
      navigate("/");
    } catch (err) {
      // Si falla, mostramos el mensaje del error; si no es un Error real,
      // usamos un texto genérico en español.
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    }
  }

  // --- Marcado (JSX) de la pantalla ---
  // Contenedor externo de la pantalla de login (toda la ventana).
  return (
    <div className="login">
      {/* Formulario: al enviarlo se dispara handleSubmit. */}
      <form onSubmit={handleSubmit} className="login-card">
        {/* Si hay logo configurado lo mostramos; si no, un recuadro con "B". */}
        {logo ? (
          <img className="login-logo" src={logo} alt="Logo" />
        ) : (
          <span className="logo-placeholder large">B</span>
        )}
        {/* Título de la aplicación. */}
        <h1>Cafetería POS</h1>
        {/* Texto de ayuda debajo del título. */}
        <p className="muted">Inicia sesión para continuar</p>
        {/* Campo de Email: es un input controlado por el estado `email`. */}
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        {/* Campo de Contraseña: input controlado por el estado `password`. */}
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {/* Solo mostramos el párrafo de error si `error` tiene contenido. */}
        {error && <p className="error">{error}</p>}
        {/* Botón que envía el formulario (type="submit"). */}
        <button type="submit" className="primary">
          Entrar
        </button>
      </form>
    </div>
  );
}
