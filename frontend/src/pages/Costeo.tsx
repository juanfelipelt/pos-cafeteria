import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney, formatNumber } from "../lib/format";

interface Resumen {
  ventas: number;
  costo_variable: number;
  margen: number;
  margen_pct: number;
  costos_fijos_mes: number;
  dias_laborables_mes: number;
  dias_laborables_rango: number;
  costo_fijo_diario: number;
  costo_fijo_periodo: number;
  utilidad: number;
  punto_equilibrio: number | null;
  faltante_equilibrio: number | null;
}

interface Margen {
  producto_id: string;
  nombre: string;
  tipo: string;
  precio: number;
  costo: number;
  margen: number;
  margen_pct: number;
  punto_equilibrio_unidades: number | null;
}

interface CostoFijo {
  id: string;
  nombre: string;
  monto: number;
  activo: boolean;
}

function hoyIso(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export default function Costeo() {
  const { user } = useAuth();
  const esAdmin = user?.rol === "admin";

  const [fecha, setFecha] = useState(hoyIso());
  const [resumen, setResumen] = useState<Resumen | null>(null);
  const [margenes, setMargenes] = useState<Margen[]>([]);
  const [costos, setCostos] = useState<CostoFijo[]>([]);

  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevoMonto, setNuevoMonto] = useState(0);
  const [editando, setEditando] = useState<CostoFijo | null>(null);
  const [error, setError] = useState("");

  async function cargar() {
    const desde = `${fecha}T00:00:00`;
    const hasta = `${fecha}T23:59:59.999`;
    const [res, marg, cos] = await Promise.all([
      api<Resumen>(`/costeo/resumen?desde=${desde}&hasta=${hasta}`),
      api<Margen[]>("/costeo/productos"),
      api<CostoFijo[]>("/costos-fijos"),
    ]);
    setResumen(res);
    setMargenes(marg);
    setCostos(cos);
  }

  useEffect(() => {
    if (!esAdmin) return;
    cargar().catch((err) =>
      setError(err instanceof Error ? err.message : "Error")
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fecha, esAdmin]);

  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  async function crearCosto(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/costos-fijos", {
        method: "POST",
        body: JSON.stringify({ nombre: nuevoNombre, monto: nuevoMonto }),
      });
      setNuevoNombre("");
      setNuevoMonto(0);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function guardarCosto() {
    if (!editando) return;
    await api(`/costos-fijos/${editando.id}`, {
      method: "PUT",
      body: JSON.stringify({
        nombre: editando.nombre,
        monto: editando.monto,
        activo: editando.activo,
      }),
    });
    setEditando(null);
    await cargar();
  }

  async function eliminarCosto(id: string) {
    if (!window.confirm("¿Eliminar este costo fijo?")) return;
    await api(`/costos-fijos/${id}`, { method: "DELETE" });
    await cargar();
  }

  const positivo = (n: number) => (n >= 0 ? "ok" : "error");

  return (
    <div>
      <div className="card-head">
        <h2 style={{ margin: 0 }}>Costeo</h2>
        <input
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
        />
      </div>

      {error && <p className="error">{error}</p>}

      {resumen && (
        <div className="cards">
          <div className="card">
            <span>Ventas del día</span>
            <strong>{formatMoney(resumen.ventas)}</strong>
            <small>
              Margen {formatMoney(resumen.margen)} ({formatNumber(resumen.margen_pct, 1)}%)
            </small>
          </div>
          <div className="card">
            <span>Costo fijo del día</span>
            <strong>{formatMoney(resumen.costo_fijo_diario)}</strong>
            <small>
              {formatMoney(resumen.costos_fijos_mes)}/mes ÷ {resumen.dias_laborables_mes} días
            </small>
          </div>
          <div className="card">
            <span>Utilidad del día</span>
            <strong className={positivo(resumen.utilidad)}>
              {formatMoney(resumen.utilidad)}
            </strong>
            <small>Costo variable {formatMoney(resumen.costo_variable)}</small>
          </div>
          <div className="card">
            <span>Punto de equilibrio</span>
            <strong>
              {resumen.punto_equilibrio === null
                ? "—"
                : formatMoney(resumen.punto_equilibrio)}
            </strong>
            <small>
              {resumen.faltante_equilibrio === null
                ? "Sin ventas aún"
                : resumen.faltante_equilibrio > 0
                ? `Faltan ${formatMoney(resumen.faltante_equilibrio)}`
                : "Equilibrio superado"}
            </small>
          </div>
        </div>
      )}

      <section className="card">
        <h3>Margen de contribución por producto</h3>
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Tipo</th>
              <th>Precio</th>
              <th>Costo</th>
              <th>Margen</th>
              <th>%</th>
              <th>Equilibrio (unid.)</th>
            </tr>
          </thead>
          <tbody>
            {margenes.map((m) => (
              <tr key={m.producto_id}>
                <td data-label="Producto" className="cell-main">
                  {m.nombre}
                </td>
                <td data-label="Tipo">{m.tipo}</td>
                <td data-label="Precio">{formatMoney(m.precio)}</td>
                <td data-label="Costo">{formatMoney(m.costo)}</td>
                <td data-label="Margen" className={positivo(m.margen)}>
                  {formatMoney(m.margen)}
                </td>
                <td data-label="%">{formatNumber(m.margen_pct, 1)}%</td>
                <td data-label="Equilibrio">
                  {m.punto_equilibrio_unidades === null
                    ? "—"
                    : formatNumber(m.punto_equilibrio_unidades, 0)}
                </td>
              </tr>
            ))}
            {margenes.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  Aún no hay productos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {esAdmin && (
        <>
          <form onSubmit={crearCosto} className="card">
            <h3>Nuevo costo fijo (mensual)</h3>
            <div className="inline-form">
              <input
                placeholder="Nombre (ej. Arriendo)"
                value={nuevoNombre}
                onChange={(e) => setNuevoNombre(e.target.value)}
                required
              />
              <MoneyInput
                placeholder="Monto mensual"
                value={nuevoMonto}
                onChange={setNuevoMonto}
              />
              <button type="submit" className="primary">
                Agregar
              </button>
            </div>
          </form>

          <section className="card">
            <h3>Costos fijos</h3>
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Monto mensual</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {costos.map((c) => (
                  <tr key={c.id}>
                    <td data-label="Nombre" className="cell-main">
                      {c.nombre}
                    </td>
                    <td data-label="Monto">{formatMoney(c.monto)}</td>
                    <td data-label="Estado">
                      <span className={c.activo ? "pill on" : "pill off"}>
                        {c.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="no-label">
                      <div className="actions">
                        <button className="ghost" onClick={() => setEditando(c)}>
                          Editar
                        </button>
                        <button
                          className="ghost danger"
                          onClick={() => eliminarCosto(c.id)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {costos.length === 0 && (
                  <tr>
                    <td colSpan={4} className="muted">
                      Aún no hay costos fijos.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        </>
      )}

      {editando && (
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar costo fijo</h3>
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
              <MoneyInput
                placeholder="Monto mensual"
                value={editando.monto}
                onChange={(v) => setEditando({ ...editando, monto: v })}
              />
              <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={editando.activo}
                  onChange={(e) =>
                    setEditando({ ...editando, activo: e.target.checked })
                  }
                />
                Activo
              </label>
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="ghost" onClick={() => setEditando(null)}>
                Cancelar
              </button>
              <button className="primary" onClick={guardarCosto}>
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
