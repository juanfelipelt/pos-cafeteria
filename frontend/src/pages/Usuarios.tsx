import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";

interface Usuario {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  estado: boolean;
}

export default function Usuarios() {
  const { user } = useAuth();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("cajero");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    setUsuarios(await api<Usuario[]>("/auth/usuarios"));
  }

  useEffect(() => {
    cargar();
  }, []);

  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setMensaje("");
    try {
      await api("/auth/registro", {
        method: "POST",
        body: JSON.stringify({ nombre, email, password, rol }),
      });
      setNombre("");
      setEmail("");
      setPassword("");
      setMensaje("Usuario creado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  return (
    <div>
      <h2>Usuarios</h2>

      <form onSubmit={crear} className="card inline-form">
        <input
          placeholder="Nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        <input
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          placeholder="Contraseña (mínimo 8 caracteres)"
          type="password"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <select value={rol} onChange={(e) => setRol(e.target.value)}>
          <option value="cajero">Cajero</option>
          <option value="admin">Administrador</option>
        </select>
        <button type="submit" className="primary">
          Crear usuario
        </button>
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </form>

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
          {usuarios.map((u) => (
            <tr key={u.id}>
              <td data-label="Nombre" className="cell-main">
                {u.nombre}
              </td>
              <td data-label="Email">{u.email}</td>
              <td data-label="Rol">
                {u.rol === "admin" ? "Administrador" : "Cajero"}
              </td>
              <td data-label="Estado">
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
