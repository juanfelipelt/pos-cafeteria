import { useEffect, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney } from "../lib/format";

interface Insumo {
  id: string;
  nombre: string;
  unidad: string;
  stock: number;
  costo_unitario: number;
  proveedor_id: string | null;
  estado: boolean;
}

interface Proveedor {
  id: string;
  nombre: string;
}

const UNIDADES = ["g", "kg", "ml", "L", "unidad", "paquete", "paca", "caja"];

export default function Insumos() {
  const { user } = useAuth();
  const esAdmin = user?.rol === "admin";

  const [insumos, setInsumos] = useState<Insumo[]>([]);
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);

  const [nombre, setNombre] = useState("");
  const [unidad, setUnidad] = useState("g");
  const [stock, setStock] = useState("");
  const [costo, setCosto] = useState(0);
  const [proveedorId, setProveedorId] = useState("");

  const [editando, setEditando] = useState<Insumo | null>(null);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  async function cargar() {
    const [ins, provs] = await Promise.all([
      api<Insumo[]>("/insumos"),
      api<Proveedor[]>("/proveedores"),
    ]);
    setInsumos(ins);
    setProveedores(provs);
  }

  useEffect(() => {
    cargar();
  }, []);

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setOk("");
    try {
      await api("/insumos", {
        method: "POST",
        body: JSON.stringify({
          nombre,
          unidad,
          stock: Number(stock) || 0,
          costo_unitario: costo,
          proveedor_id: proveedorId || null,
        }),
      });
      setNombre("");
      setUnidad("g");
      setStock("");
      setCosto(0);
      setProveedorId("");
      setOk("Insumo creado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function guardarEdicion() {
    if (!editando) return;
    setError("");
    try {
      await api(`/insumos/${editando.id}`, {
        method: "PUT",
        body: JSON.stringify({
          nombre: editando.nombre,
          unidad: editando.unidad,
          stock: editando.stock,
          costo_unitario: editando.costo_unitario,
          proveedor_id: editando.proveedor_id,
        }),
      });
      setEditando(null);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function cambiarEstado(i: Insumo) {
    await api(`/insumos/${i.id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: !i.estado }),
    });
    await cargar();
  }

  async function eliminar(i: Insumo) {
    if (!window.confirm(`¿Eliminar el insumo "${i.nombre}"?`)) return;
    setError("");
    try {
      await api(`/insumos/${i.id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  const proveedorDe = (id: string | null) =>
    proveedores.find((p) => p.id === id)?.nombre ?? "—";

  return (
    <div>
      <h2>Insumos</h2>

      {esAdmin && (
        <form onSubmit={crear} className="card">
          <h3>Nuevo insumo</h3>
          <div className="inline-form">
            <input
              placeholder="Nombre (ej. Café molido)"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />
            <select value={unidad} onChange={(e) => setUnidad(e.target.value)}>
              {UNIDADES.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
            <input
              placeholder="Stock"
              type="number"
              step="any"
              value={stock}
              onChange={(e) => setStock(e.target.value)}
            />
            <MoneyInput placeholder="Costo unitario" value={costo} onChange={setCosto} />
            <select
              value={proveedorId}
              onChange={(e) => setProveedorId(e.target.value)}
            >
              <option value="">Sin proveedor</option>
              {proveedores.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" className="primary">
              Guardar
            </button>
          </div>
          {ok && <p className="ok">{ok}</p>}
          {error && <p className="error">{error}</p>}
        </form>
      )}

      {!esAdmin && error && <p className="error">{error}</p>}

      <section className="card">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Unidad</th>
              <th>Stock</th>
              <th>Costo unitario</th>
              <th>Proveedor</th>
              <th>Estado</th>
              {esAdmin && <th></th>}
            </tr>
          </thead>
          <tbody>
            {insumos.map((i) => (
              <tr key={i.id}>
                <td data-label="Nombre" className="cell-main">
                  {i.nombre}
                </td>
                <td data-label="Unidad">{i.unidad}</td>
                <td data-label="Stock">{i.stock}</td>
                <td data-label="Costo unitario">{formatMoney(i.costo_unitario)}</td>
                <td data-label="Proveedor">{proveedorDe(i.proveedor_id)}</td>
                <td data-label="Estado">
                  <span className={i.estado ? "pill on" : "pill off"}>
                    {i.estado ? "Activo" : "Inactivo"}
                  </span>
                </td>
                {esAdmin && (
                  <td className="no-label">
                    <div className="actions">
                      <button className="ghost" onClick={() => setEditando(i)}>
                        Editar
                      </button>
                      <button className="ghost" onClick={() => cambiarEstado(i)}>
                        {i.estado ? "Desactivar" : "Activar"}
                      </button>
                      <button
                        className="ghost danger"
                        onClick={() => eliminar(i)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {insumos.length === 0 && (
              <tr>
                <td colSpan={esAdmin ? 7 : 6} className="muted">
                  Aún no hay insumos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {editando && (
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar insumo</h3>
            <div
              className="inline-form"
              style={{ flexDirection: "column", alignItems: "stretch" }}
            >
              <input
                placeholder="Nombre"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
              <select
                value={editando.unidad}
                onChange={(e) =>
                  setEditando({ ...editando, unidad: e.target.value })
                }
              >
                {UNIDADES.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
              <input
                placeholder="Stock"
                type="number"
                step="any"
                value={editando.stock}
                onChange={(e) =>
                  setEditando({ ...editando, stock: Number(e.target.value) })
                }
              />
              <MoneyInput
                placeholder="Costo unitario"
                value={editando.costo_unitario}
                onChange={(v) =>
                  setEditando({ ...editando, costo_unitario: v })
                }
              />
              <select
                value={editando.proveedor_id ?? ""}
                onChange={(e) =>
                  setEditando({
                    ...editando,
                    proveedor_id: e.target.value || null,
                  })
                }
              >
                <option value="">Sin proveedor</option>
                {proveedores.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
              </select>
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
