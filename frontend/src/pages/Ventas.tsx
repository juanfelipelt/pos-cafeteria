import { Fragment, useEffect, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney } from "../lib/format";

interface Detalle {
  id: string;
  producto_id: string;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

interface Pago {
  id: string;
  monto: number;
  metodo: string;
  fecha: string;
  referencia: string | null;
}

interface Venta {
  id: string;
  usuario_id: string | null;
  fecha: string;
  detalles: Detalle[];
  pagos: Pago[];
  total: number;
  total_pagado: number;
  pendiente: number;
  esta_pagada: boolean;
  anulada: boolean;
}

function estado(v: Venta): { label: string; clase: string } {
  if (v.anulada) return { label: "Anulada", clase: "off" };
  if (v.esta_pagada) return { label: "Pagada", clase: "on" };
  return { label: "Parcial", clase: "off" };
}

function fecha(v: Venta): string {
  return new Date(v.fecha).toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Ventas() {
  const { user } = useAuth();
  const [ventas, setVentas] = useState<Venta[]>([]);
  const [abierta, setAbierta] = useState<string | null>(null);
  const [pagoMonto, setPagoMonto] = useState(0);
  const [pagoMetodo, setPagoMetodo] = useState("efectivo");
  const [error, setError] = useState("");

  async function cargar() {
    setVentas(await api<Venta[]>("/ventas"));
  }

  useEffect(() => {
    cargar();
  }, []);

  async function anular(id: string) {
    setError("");
    try {
      await api(`/ventas/${id}/anular`, { method: "POST" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al anular");
    }
  }

  async function eliminar(id: string) {
    if (!window.confirm("¿Eliminar esta venta? Se reintegrará el stock.")) return;
    setError("");
    try {
      await api(`/ventas/${id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    }
  }

  async function registrarPago(id: string) {
    if (pagoMonto <= 0) return;
    setError("");
    try {
      await api(`/ventas/${id}/pagos`, {
        method: "POST",
        body: JSON.stringify({ monto: pagoMonto, metodo: pagoMetodo }),
      });
      setPagoMonto(0);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar pago");
    }
  }

  return (
    <div>
      <h2>Ventas</h2>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Total</th>
            <th>Estado</th>
            {user?.rol === "admin" && <th></th>}
          </tr>
        </thead>
        <tbody>
          {ventas.map((v) => (
            <Fragment key={v.id}>
              <tr
                className="venta-row"
                onClick={() => setAbierta(abierta === v.id ? null : v.id)}
              >
                <td>{fecha(v)}</td>
                <td>{formatMoney(v.total)}</td>
                <td>
                  <span className={`pill ${estado(v).clase}`}>
                    {estado(v).label}
                  </span>
                </td>
                {user?.rol === "admin" && (
                  <td onClick={(e) => e.stopPropagation()}>
                    {!v.anulada && (
                      <button className="ghost" onClick={() => anular(v.id)}>
                        Anular
                      </button>
                    )}
                    <button
                      className="ghost"
                      style={{ marginLeft: 8 }}
                      onClick={() => eliminar(v.id)}
                    >
                      Eliminar
                    </button>
                  </td>
                )}
              </tr>
              {abierta === v.id && (
                <tr>
                  <td colSpan={user?.rol === "admin" ? 4 : 3}>
                    <div className="detail-panel">
                      {v.detalles.map((d) => (
                        <div
                          key={d.id}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "3px 0",
                          }}
                        >
                          <span>
                            {d.nombre_producto} × {d.cantidad}
                          </span>
                          <span>{formatMoney(d.subtotal)}</span>
                        </div>
                      ))}

                      {v.pagos.length > 0 && (
                        <div
                          style={{
                            marginTop: 8,
                            borderTop: "1px solid var(--border)",
                            paddingTop: 8,
                          }}
                        >
                          {v.pagos.map((p) => (
                            <div
                              key={p.id}
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                              }}
                            >
                              <span>{p.metodo}</span>
                              <span>{formatMoney(p.monto)}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {!v.anulada && !v.esta_pagada && (
                        <div
                          style={{
                            marginTop: 12,
                            borderTop: "1px solid var(--border)",
                            paddingTop: 12,
                          }}
                        >
                          <p style={{ margin: "0 0 8px" }}>
                            Pendiente:{" "}
                            <strong>{formatMoney(v.pendiente)}</strong>
                          </p>
                          <div className="payment">
                            <MoneyInput
                              placeholder="Monto"
                              value={pagoMonto}
                              onChange={setPagoMonto}
                            />
                            <select
                              value={pagoMetodo}
                              onChange={(e) => setPagoMetodo(e.target.value)}
                            >
                              <option value="efectivo">Efectivo</option>
                              <option value="tarjeta">Tarjeta</option>
                              <option value="transferencia">Transferencia</option>
                            </select>
                            <button
                              className="primary"
                              onClick={() => registrarPago(v.id)}
                            >
                              Registrar pago
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
