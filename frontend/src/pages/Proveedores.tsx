import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";

const TIPOS_IDENTIFICACION = [
  "CC",
  "NIT",
  "CE",
  "TI",
  "PPT",
  "PASAPORTE",
  "OTRO",
];

interface Proveedor {
  id: string;
  nombre: string;
  contacto: string;
  telefono: string;
  email: string;
  direccion: string;
  tipo_identificacion: string;
  identificacion: string;
  estado: boolean;
}

interface Editando {
  id: string;
  nombre: string;
  contacto: string;
  telefono: string;
  email: string;
  direccion: string;
  tipo_identificacion: string;
  identificacion: string;
}

export default function Proveedores() {
  const { user } = useAuth();
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [nombre, setNombre] = useState("");
  const [contacto, setContacto] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [tipoId, setTipoId] = useState("");
  const [identificacion, setIdentificacion] = useState("");
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
        body: JSON.stringify({
          nombre,
          contacto,
          telefono,
          email,
          tipo_identificacion: tipoId,
          identificacion,
        }),
      });
      setNombre("");
      setContacto("");
      setTelefono("");
      setEmail("");
      setTipoId("");
      setIdentificacion("");
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
          tipo_identificacion: editando.tipo_identificacion,
          identificacion: editando.identificacion,
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

  const ident = (p: Proveedor) =>
    p.identificacion ? `${p.tipo_identificacion || "—"} ${p.identificacion}` : "—";

  return (
    <div>
      <h2>Proveedores</h2>

      {error && <p className="error">{error}</p>}

      {user?.rol === "admin" && (
        <form onSubmit={crear} className="card">
          <h3>Nuevo proveedor</h3>
        <div className="inline-form">
          <select value={tipoId} onChange={(e) => setTipoId(e.target.value)}>
            <option value="" disabled>
              Tipo identificación
            </option>
            {TIPOS_IDENTIFICACION.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <input
            placeholder="N° identificación"
            value={identificacion}
            onChange={(e) => setIdentificacion(e.target.value)}
          />
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
          <input
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button type="submit" className="primary">
            Agregar
          </button>
        </div>
        {ok && <p className="ok">{ok}</p>}
      </form>
      )}

      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Identificación</th>
            <th>Contacto</th>
            <th>Teléfono</th>
            <th>Email</th>
            <th>Estado</th>
            {user?.rol === "admin" && <th></th>}
          </tr>
        </thead>
        <tbody>
          {proveedores.map((p) => (
            <tr key={p.id}>
              <td data-label="Nombre" className="cell-main">
                {p.nombre}
              </td>
              <td data-label="Identificación">{ident(p)}</td>
              <td data-label="Contacto">{p.contacto}</td>
              <td data-label="Teléfono">{p.telefono}</td>
              <td data-label="Email">{p.email || "—"}</td>
              <td data-label="Estado">
                <span className={p.estado ? "pill on" : "pill off"}>
                  {p.estado ? "Activo" : "Inactivo"}
                </span>
              </td>
              {user?.rol === "admin" && (
                <td className="no-label">
                  <div className="actions">
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
                          tipo_identificacion: p.tipo_identificacion,
                          identificacion: p.identificacion,
                        })
                      }
                    >
                      Editar
                    </button>
                    <button
                      className="ghost"
                      onClick={() => cambiarEstado(p)}
                    >
                      {p.estado ? "Desactivar" : "Activar"}
                    </button>
                    <button
                      className="ghost danger"
                      onClick={() => eliminar(p.id)}
                    >
                      Eliminar
                    </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {editando && (
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar proveedor</h3>
            <div className="inline-form" style={{ flexDirection: "column", alignItems: "stretch" }}>
              <select
                value={editando.tipo_identificacion}
                onChange={(e) =>
                  setEditando({ ...editando, tipo_identificacion: e.target.value })
                }
              >
                <option value="" disabled>
                  Tipo identificación
                </option>
                {TIPOS_IDENTIFICACION.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <input
                placeholder="N° identificación"
                value={editando.identificacion}
                onChange={(e) =>
                  setEditando({ ...editando, identificacion: e.target.value })
                }
              />
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
