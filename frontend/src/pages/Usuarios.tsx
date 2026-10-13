/*
 * ============================================================================
 * PÁGINA: Usuarios
 * ============================================================================
 * ¿Qué es este archivo?
 *   Es la pantalla de administración de usuarios. Permite crear cuentas
 *   nuevas (con nombre, correo, contraseña y rol) y ver en una tabla todos
 *   los usuarios registrados con su rol y estado.
 *
 * ¿Para qué sirve?
 *   Solo el administrador puede dar de alta a los cajeros y a otros admins
 *   desde aquí, controlando quién puede entrar al sistema.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Usa `api` (../api) para listar usuarios (/auth/usuarios) y crear
 *     cuentas (/auth/registro).
 *   - Usa `useAuth` (../auth) para verificar que el usuario sea administrador;
 *     si no lo es, se le redirige al inicio.
 *   - Los usuarios creados aquí son los mismos que luego inician sesión y
 *     cuyos roles (admin/cajero) usan las demás pantallas para sus permisos.
 * ============================================================================
 */

import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";

// Un usuario tal como lo devuelve el backend (sin la contraseña, por seguridad).
interface Usuario {
  id: string; // Identificador único.
  nombre: string; // Nombre completo de la persona.
  email: string; // Correo con el que inicia sesión.
  rol: string; // "admin" o "cajero".
  estado: boolean; // Si la cuenta está activa o deshabilitada.
}

export default function Usuarios() {
  const { user } = useAuth();

  // ------------------------------ ESTADO ---------------------------------
  const [usuarios, setUsuarios] = useState<Usuario[]>([]); // Lista de usuarios.
  // Campos del formulario para crear un usuario nuevo.
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("cajero"); // Por defecto creamos cajeros.
  // Mensajes de éxito y de error por separado.
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  // Trae la lista de usuarios desde el backend y la guarda en el estado.
  async function cargar() {
    setUsuarios(await api<Usuario[]>("/auth/usuarios"));
  }

  // EFECTO: al entrar a la pantalla por primera vez, cargamos los usuarios.
  // El arreglo vacío [] significa que solo se ejecuta una vez al montar.
  useEffect(() => {
    cargar();
  }, []);

  // GUARDA DE SEGURIDAD: solo administradores; el resto va al inicio.
  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  // Crea un usuario nuevo con los datos del formulario.
  async function crear(e: React.FormEvent) {
    e.preventDefault(); // Evita que el navegador recargue la página.
    setError("");
    setMensaje("");
    try {
      await api("/auth/registro", {
        method: "POST",
        body: JSON.stringify({ nombre, email, password, rol }),
      });
      // Limpiamos el formulario (mantenemos el rol por comodidad).
      setNombre("");
      setEmail("");
      setPassword("");
      setMensaje("Usuario creado.");
      await cargar(); // Refrescamos la tabla.
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  return (
    <div>
      <h2>Usuarios</h2>

      {/* Formulario para crear un usuario nuevo. */}
      <form onSubmit={crear} className="card inline-form">
        <input
          placeholder="Nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        {/* type="email" valida el formato del correo automáticamente. */}
        <input
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        {/* minLength={8} exige una contraseña de al menos 8 caracteres. */}
        <input
          placeholder="Contraseña (mínimo 8 caracteres)"
          type="password"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {/* Selector del rol que tendrá la nueva cuenta. */}
        <select value={rol} onChange={(e) => setRol(e.target.value)}>
          <option value="cajero">Cajero</option>
          <option value="admin">Administrador</option>
        </select>
        <button type="submit" className="primary">
          Crear usuario
        </button>
        {/* Mensaje verde si se creó bien y rojo si hubo un problema. */}
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </form>

      {/* Tabla con todos los usuarios registrados. */}
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {/* Una fila por cada usuario de la lista. */}
          {usuarios.map((u) => (
            <tr key={u.id}>
              <td data-label="Nombre" className="cell-main">
                {u.nombre}
              </td>
              <td data-label="Email">{u.email}</td>
              <td data-label="Rol">
                {/* Traducimos el rol interno a un texto más claro. */}
                {u.rol === "admin" ? "Administrador" : "Cajero"}
              </td>
              <td data-label="Estado">
                {/* Etiqueta verde si está activo, gris si está inactivo. */}
                <span className={u.estado ? "pill on" : "pill off"}>
                  {u.estado ? "Activo" : "Inactivo"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
