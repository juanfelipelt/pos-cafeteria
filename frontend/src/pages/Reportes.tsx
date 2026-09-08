import { useState } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { formatMoney, formatNumber } from "../lib/format";

interface Punto {
  periodo: string;
  total: number;
  num_ventas: number;
}

export default function Reportes() {
  const [desde, setDesde] = useState(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1)
      .toISOString()
      .slice(0, 10)
  );
  const [hasta, setHasta] = useState(new Date().toISOString().slice(0, 10));
  const [agrupacion, setAgrupacion] = useState("dia");
  const [data, setData] = useState<Punto[]>([]);
  const [error, setError] = useState("");

  async function consultar() {
    setError("");
    try {
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
        <select
          value={agrupacion}
          onChange={(e) => setAgrupacion(e.target.value)}
        >
          <option value="dia">Por día</option>
          <option value="semana">Por semana</option>
          <option value="mes">Por mes</option>
          <option value="año">Por año</option>
        </select>
        <button className="primary" onClick={consultar}>
          Consultar
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      {data.length > 0 && (
        <div className="grid">
          <section className="card">
            <h3>Facturación por {agrupacion}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data}>
                <XAxis dataKey="periodo" tickLine={false} axisLine={false} />
                <YAxis
                  tickFormatter={(v) => formatNumber(Number(v), 0)}
                  tickLine={false}
                  axisLine={false}
                  width={60}
                />
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                  formatter={(value) => [
                    formatMoney(Number(value)),
                    "Total",
                  ]}
                />
                <Bar dataKey="total" fill="#37352f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>

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
