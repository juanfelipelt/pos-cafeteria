/*
 * Ventas.tsx — Pantalla de "Ventas" (historial y gestión de ventas).
 *
 * ¿Qué es?
 *   Es la pantalla donde se consultan todas las ventas registradas en el
 *   sistema (las que se crean desde el POS).
 *
 * ¿Para qué sirve?
 *   - Listar las ventas con su fecha, total y estado (Pagada / Parcial / Anulada).
 *   - Desplegar el detalle de una venta: productos vendidos y pagos recibidos.
 *   - Registrar pagos parciales cuando una venta quedó pendiente.
 *   - (Solo administradores) Anular o eliminar una venta.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se monta en la ruta "/ventas" (ver App.tsx), protegida por login.
 *   - Las ventas que se muestran aquí son las que crea POS.tsx mediante
 *     el endpoint POST /ventas.
 *   - Usa `useAuth` para saber el rol del usuario: los botones de admin solo
 *     aparecen si `user.rol === "admin"`.
 *   - Reutiliza `MoneyInput` (capturar montos) y `formatMoney` (mostrarlos).
 *   - Habla con el backend a través de `api` (api.ts).
 */

// Fragment permite agrupar dos filas hermanas (<tr>) sin crear un nodo extra.
import { Fragment, useEffect, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney } from "../lib/format";

// Una línea de la venta (un producto y su cantidad / precio / subtotal).
interface Detalle {
  id: string;
  producto_id: string;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

// Un pago realizado sobre la venta (puede haber varios, pagos parciales).
interface Pago {
  id: string;
  monto: number;
  metodo: string;
  fecha: string;
  referencia: string | null;
}

// Una venta completa tal como la devuelve el backend.
interface Venta {
  id: string;
  usuario_id: string | null; // quién la registró (null = sistema/desconocido)
  fecha: string; // fecha en formato ISO
  detalles: Detalle[]; // productos vendidos
  pagos: Pago[]; // pagos recibidos
  total: number; // total de la venta
  total_pagado: number; // cuánto se ha pagado hasta ahora
  pendiente: number; // total - total_pagado
  esta_pagada: boolean; // ¿ya se pagó completa?
  anulada: boolean; // ¿fue anulada?
}

// Calcula la etiqueta y el color del estado de una venta.
// Prioridad: primero anulada, luego pagada, y si no, queda "Parcial".
function estado(v: Venta): { label: string; clase: string } {
  if (v.anulada) return { label: "Anulada", clase: "off" };
  if (v.esta_pagada) return { label: "Pagada", clase: "on" };
  return { label: "Parcial", clase: "off" };
}

// Convierte la fecha ISO del backend a un texto legible (dd/mm/aaaa hh:mm).
function fecha(v: Venta): string {
  return new Date(v.fecha).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Componente principal de la pantalla de Ventas.
export default function Ventas() {
  // `user` nos da el usuario logueado; lo usamos para saber si es admin.
  const { user } = useAuth();
  const [ventas, setVentas] = useState<Venta[]>([]); // lista de ventas
  const [abierta, setAbierta] = useState<string | null>(null); // id de la venta desplegada
  const [pagoMonto, setPagoMonto] = useState(0); // monto del nuevo pago
  const [pagoMetodo, setPagoMetodo] = useState("efectivo"); // método del nuevo pago
  const [error, setError] = useState(""); // mensaje de error

  // Pide al backend todas las ventas y actualiza el estado.
  async function cargar() {
    setVentas(await api<Venta[]>("/ventas"));
  }

  // Al montar la pantalla, cargamos las ventas una sola vez.
  useEffect(() => {
    cargar();
  }, []);

  // Anula una venta (normalmente reintegra el stock en el backend).
  async function anular(id: string) {
    setError("");
    try {
      await api(`/ventas/${id}/anular`, { method: "POST" });
      await cargar(); // recargamos para ver el nuevo estado
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al anular");
    }
  }

  // Elimina definitivamente una venta. Pide confirmación primero porque
  // es una acción peligrosa e irreversible.
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

  // Registra un pago parcial para una venta pendiente.
  async function registrarPago(id: string) {
    if (pagoMonto <= 0) return; // no tiene sentido pagar 0 o negativos
    setError("");
    try {
      await api(`/ventas/${id}/pagos`, {
        method: "POST",
        body: JSON.stringify({ monto: pagoMonto, metodo: pagoMetodo }),
      });
      setPagoMonto(0); // limpiamos el monto tras un pago exitoso
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar pago");
    }
  }

  // Marcado que se dibuja en pantalla.
  return (
    <div>
      <h2>Ventas</h2>

      {/* Mostramos el error solo si existe. */}
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Total</th>
            <th>Estado</th>
            {/* La columna de acciones solo existe para administradores. */}
            {user?.rol === "admin" && <th></th>}
          </tr>
        </thead>
        <tbody>
          {ventas.map((v) => (
            // Fragment agrupa la fila de la venta y su fila de detalle.
            <Fragment key={v.id}>
              {/* Fila principal: al hacer clic, abre/cierra el detalle. */}
              <tr
                className="venta-row"
                onClick={() => setAbierta(abierta === v.id ? null : v.id)}
              >
                <td data-label="Fecha">{fecha(v)}</td>
                <td data-label="Total">{formatMoney(v.total)}</td>
                <td data-label="Estado">
                  {/* Píldora de color según el estado calculado. */}
                  <span className={`pill ${estado(v).clase}`}>
                    {estado(v).label}
                  </span>
                </td>
                {/* Celda de acciones (solo admin). stopPropagation evita que
                    el clic en los botones abra/cierre el detalle de la fila. */}
                {user?.rol === "admin" && (
                  <td className="no-label" onClick={(e) => e.stopPropagation()}>
                    <div className="actions">
                      {/* Solo se puede anular si no está anulada ya. */}
                      {!v.anulada && (
                        <button className="ghost" onClick={() => anular(v.id)}>
                          Anular
                        </button>
                      )}
                      <button
                        className="ghost danger"
                        onClick={() => eliminar(v.id)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                )}
              </tr>
              {/* Fila de detalle: solo se muestra si esta venta está abierta. */}
              {abierta === v.id && (
                <tr className="detalle-row">
                  {/* colSpan ajusta el ancho: 4 columnas con admin, 3 sin admin. */}
                  <td colSpan={user?.rol === "admin" ? 4 : 3}>
                    <div className="detail-panel">
                      {/* Lista de productos vendidos con su subtotal. */}
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

                      {/* Lista de pagos, solo si la venta tiene alguno. */}
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

                      {/* Sección para pagar el saldo: solo si la venta no
                          está anulada ni totalmente pagada. */}
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
                            {/* Monto a pagar. */}
                            <MoneyInput
                              placeholder="Monto"
                              value={pagoMonto}
                              onChange={setPagoMonto}
                            />
                            {/* Método del pago. */}
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
