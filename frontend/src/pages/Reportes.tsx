/*
 * ============================================================================
 * PÁGINA: Reportes
 * ============================================================================
 * ¿Qué es este archivo?
 *   Es la pantalla de informes de ventas. Permite elegir un rango de fechas
 *   (desde/hasta) y cómo agrupar los datos (por día, semana, mes o año), y
 *   muestra un gráfico de barras con la facturación junto a una tabla detalle.
 *
 * ¿Para qué sirve?
 *   Ayuda al administrador a ver cómo evolucionan las ventas en el tiempo y
 *   detectar los mejores y peores períodos.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Usa `api` (../api) para pedir los totales al backend
 *     (/reportes/ventas).
 *   - Usa la librería `recharts` para dibujar el gráfico de barras.
 *   - Usa `useAuth` (../auth) para permitir la entrada solo a administradores.
 *   - Usa `formatMoney`/`formatNumber` (../lib/format) para mostrar montos.
 *   - El gráfico se alimenta de las mismas ventas que registra la caja.
 * ============================================================================
 */

import { useState } from "react";
import { Navigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { useAuth } from "../auth";
import { formatMoney, formatNumber } from "../lib/format";

// Cada punto del reporte: un período con su total y cuántas ventas hubo.
interface Punto {
  periodo: string; // Etiqueta del período (ej. "2026-10-12" o "2026-10").
  total: number; // Suma de dinero vendido en ese período.
  num_ventas: number; // Cantidad de ventas realizadas en ese período.
}

export default function Reportes() {
  const { user } = useAuth();

  // ------------------------------ ESTADO ---------------------------------
  // Fecha inicial: por defecto el primer día del mes actual. Se arma con
  // Date y se recorta a "AAAA-MM-DD" para el input de tipo date.
  const [desde, setDesde] = useState(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1)
      .toISOString()
      .slice(0, 10)
  );
  // Fecha final: por defecto hoy (mismo truncado a "AAAA-MM-DD").
  const [hasta, setHasta] = useState(new Date().toISOString().slice(0, 10));
  // Cómo agrupar los resultados: "dia", "semana", "mes" o "año".
  const [agrupacion, setAgrupacion] = useState("dia");
  // Datos ya consultados que alimentan el gráfico y la tabla.
  const [data, setData] = useState<Punto[]>([]);
  // Mensaje de error si la consulta falla.
  const [error, setError] = useState("");

  // GUARDA DE SEGURIDAD: solo los administradores entran; el resto va al inicio.
  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  // Pide al backend los totales de ventas según rango y agrupación elegidos.
  async function consultar() {
    setError("");
    try {
      // El backend recibe un rango completo del día (00:00 a 23:59) para
      // incluir todas las ventas de las fechas límite.
      const puntos = await api<Punto[]>(
        `/reportes/ventas?desde=${desde}T00:00:00&hasta=${hasta}T23:59:59&agrupacion=${agrupacion}`
      );
      setData(puntos);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  return (
    <div>
      <h2>Reportes</h2>

      {/* Panel de filtros: fechas, agrupación y botón consultar. */}
      <div className="card inline-form">
        <label>
          Desde
          <input
            type="date"
            value={desde}
            onChange={(e) => setDesde(e.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={hasta}
            onChange={(e) => setHasta(e.target.value)}
          />
        </label>
        {/* Selector de agrupación temporal. */}
        <select
          value={agrupacion}
          onChange={(e) => setAgrupacion(e.target.value)}
        >
          <option value="dia">Por día</option>
          <option value="semana">Por semana</option>
          <option value="mes">Por mes</option>
          <option value="año">Por año</option>
        </select>
        {/* Al pulsar "Consultar" se hace la petición al backend. */}
        <button className="primary" onClick={consultar}>
          Consultar
        </button>
        {/* Error mostrado dentro del panel de filtros. */}
        {error && <p className="error">{error}</p>}
      </div>

      {/* Solo dibujamos gráfico y tabla si hay datos (data.length > 0). */}
      {data.length > 0 && (
        <div className="grid">
          {/* Gráfico de barras de facturación. */}
          <section className="card">
            <h3>Facturación por {agrupacion}</h3>
            {/* ResponsiveContainer hace que el gráfico se adapte al ancho. */}
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data}>
                {/* Eje X: los períodos. */}
                <XAxis dataKey="periodo" tickLine={false} axisLine={false} />
                {/* Eje Y: totales, formateados sin decimales. */}
                <YAxis
                  tickFormatter={(v) => formatNumber(Number(v), 0)}
                  tickLine={false}
                  axisLine={false}
                  width={60}
                />
                {/* Tooltip: al pasar el mouse muestra el monto con formato $. */}
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                  formatter={(value) => [
                    formatMoney(Number(value)),
                    "Total",
                  ]}
                />
                {/* La barra representa el campo "total" de cada punto. */}
                <Bar dataKey="total" fill="#37352f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>

          {/* Tabla detalle con los mismos datos del gráfico. */}
          <section className="card">
            <h3>Detalle</h3>
            <table>
              <thead>
                <tr>
                  <th>Periodo</th>
                  <th>Ventas</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {/* Una fila por cada período consultado. */}
                {data.map((d) => (
                  <tr key={d.periodo}>
                    <td data-label="Periodo" className="cell-main">
                      {d.periodo}
                    </td>
                    <td data-label="Ventas">{d.num_ventas}</td>
                    <td data-label="Total">{formatMoney(d.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      )}
    </div>
  );
}
