import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";

interface Proveedor {
  id: string;
  nombre: string;
  contacto: string;
  telefono: string;
  email: string;
  direccion: string;
  estado: boolean;
}

interface Editando {
  id: string;
  nombre: string;
  contacto: string;
  telefono: string;
  email: string;
  direccion: string;
}

export default function Proveedores() {
  const { user } = useAuth();
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [nombre, setNombre] = useState("");
  const [contacto, setContacto] = useState("");
  const [telefono, setTelefono] = useState("");
  const [editando, setEditando] = useState<Editando | null>(null);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  async function cargar() {
    setProveedores(await api<Proveedor[]>("/proveedores"));
  }

  useEffect(() => {
    cargar();
  }, []);

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setOk("");
    try {
      await api("/proveedores", {
        method: "POST",
        body: JSON.stringify({ nombre, contacto, telefono }),
      });
      setNombre("");
      setContacto("");
      setTelefono("");
      setOk("Proveedor creado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function guardarEdicion() {
    if (!editando) return;
    setError("");
    try {
      await api(`/proveedores/${editando.id}`, {
        method: "PUT",
        body: JSON.stringify({
          nombre: editando.nombre,
          contacto: editando.contacto,
          telefono: editando.telefono,
          email: editando.email,
          direccion: editando.direccion,
        }),
      });
      setEditando(null);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function cambiarEstado(p: Proveedor) {
    await api(`/proveedores/${p.id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: !p.estado }),
    });
    await cargar();
  }

  async function eliminar(id: string) {
    if (!window.confirm("¿Eliminar este proveedor?")) return;
    setError("");
    try {
      await api(`/proveedores/${id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  return (
    <div>
      <h2>Proveedores</h2>

      <form onSubmit={crear} className="card inline-form">
        <input
          placeholder="Nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        <input
          placeholder="Contacto"
          value={contacto}
          onChange={(e) => setContacto(e.target.value)}
          required
        />
        <input
          placeholder="Teléfono"
          value={telefono}
          onChange={(e) => setTelefono(e.target.value)}
          required
        />
        <button type="submit" className="primary">
          Agregar
        </button>
        {ok && <p className="ok">{ok}</p>}
        {error && <p className="error">{error}</p>}
      </form>

      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Contacto</th>
            <th>Teléfono</th>
            <th>Email</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {proveedores.map((p) => (
            <tr key={p.id}>
              <td>{p.nombre}</td>
              <td>{p.contacto}</td>
              <td>{p.telefono}</td>
              <td>{p.email || "—"}</td>
              <td>
                <span className={p.estado ? "pill on" : "pill off"}>
                  {p.estado ? "Activo" : "Inactivo"}
                </span>
              </td>
              <td>
                <button
                  className="ghost"
                  onClick={() =>
                    setEditando({
                      id: p.id,
                      nombre: p.nombre,
                      contacto: p.contacto,
                      telefono: p.telefono,
                      email: p.email,
                      direccion: p.direccion,
                    })
                  }
                >
                  Editar
                </button>
                <button
                  className="ghost"
                  style={{ marginLeft: 6 }}
                  onClick={() => cambiarEstado(p)}
                >
                  {p.estado ? "Desactivar" : "Activar"}
                </button>
                {user?.rol === "admin" && (
                  <button
                    className="ghost"
                    style={{ marginLeft: 6 }}
                    onClick={() => eliminar(p.id)}
                  >
                    Eliminar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {editando && (
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar proveedor</h3>
            <div className="inline-form" style={{ flexDirection: "column", alignItems: "stretch" }}>
              <input
                placeholder="Nombre"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
              <input
                placeholder="Contacto"
                value={editando.contacto}
                onChange={(e) =>
                  setEditando({ ...editando, contacto: e.target.value })
                }
              />
              <input
                placeholder="Teléfono"
                value={editando.telefono}
                onChange={(e) =>
                  setEditando({ ...editando, telefono: e.target.value })
                }
              />
              <input
                placeholder="Email"
                value={editando.email}
                onChange={(e) =>
                  setEditando({ ...editando, email: e.target.value })
                }
              />
              <input
                placeholder="Dirección"
                value={editando.direccion}
                onChange={(e) =>
                  setEditando({ ...editando, direccion: e.target.value })
                }
              />
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="ghost" onClick={() => setEditando(null)}>
                Cancelar
              </button>
              <button className="primary" onClick={guardarEdicion}>
                Guardar
              </button>
            </div>
            {error && <p className="error">{error}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
