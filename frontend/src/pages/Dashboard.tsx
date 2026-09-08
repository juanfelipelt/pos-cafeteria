import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, eventSourceUrl, getToken } from "../api";
import { formatMoney, formatNumber } from "../lib/format";

interface Resumen {
  total: number;
  num_ventas: number;
}

interface TopProducto {
  producto_id: string;
  nombre: string;
  cantidad: number;
  monto: number;
}

interface Evento {
  type: string;
  data: { id: string; total: number; fecha: string };
}

function inicioDia(d: Date): string {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x.toISOString().slice(0, 19);
}

function ahora(): string {
  return new Date().toISOString().slice(0, 19);
}

export default function Dashboard() {
  const [resumenHoy, setResumenHoy] = useState<Resumen | null>(null);
  const [resumenMes, setResumenMes] = useState<Resumen | null>(null);
  const [top, setTop] = useState<TopProducto[]>([]);
  const [eventos, setEventos] = useState<Evento[]>([]);

  async function cargar() {
    const hoy = inicioDia(new Date());
    const ahoraIso = ahora();
    const [rh, rm, tp] = await Promise.all([
      api<Resumen>(`/reportes/resumen?desde=${hoy}&hasta=${ahoraIso}`),
      api<Resumen>(
        `/reportes/resumen?desde=${new Date(
          new Date().getFullYear(),
          new Date().getMonth(),
          1
        )
          .toISOString()
          .slice(0, 19)}&hasta=${ahoraIso}`
      ),
      api<TopProducto[]>(
        `/reportes/top-productos?desde=${hoy}&hasta=${ahoraIso}&limite=10`
      ),
    ]);
    setResumenHoy(rh);
    setResumenMes(rm);
    setTop(tp);
  }

  useEffect(() => {
    cargar();

    const es = new EventSource(
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as Evento;
      setEventos((prev) => [msg, ...prev].slice(0, 10));
      if (msg.type === "venta_creada" || msg.type === "venta_anulada") {
        cargar();
      }
    };
    return () => es.close();
  }, []);

  const data = top.map((t) => ({ name: t.nombre, vendidos: t.cantidad }));
  const dataMonto = top.map((t) => ({ name: t.nombre, monto: t.monto }));

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="cards">
        <div className="card">
          <span>Facturado hoy</span>
          <strong>{formatMoney(resumenHoy?.total ?? 0)}</strong>
          <small>{resumenHoy?.num_ventas ?? 0} ventas</small>
        </div>
        <div className="card">
          <span>Facturado este mes</span>
          <strong>{formatMoney(resumenMes?.total ?? 0)}</strong>
          <small>{resumenMes?.num_ventas ?? 0} ventas</small>
        </div>
      </div>

      <div className="grid">
        <section className="card">
          <h3>Más vendidos (cantidad)</h3>
          {data.length === 0 ? (
            <p className="muted">Sin ventas aún.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data}>
                <XAxis dataKey="name" tickLine={false} axisLine={false} />
                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                  formatter={(value) => [formatNumber(Number(value)), "Unidades"]}
                />
                <Bar dataKey="vendidos" fill="#37352f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        <section className="card">
          <h3>Más vendidos ($)</h3>
          {dataMonto.length === 0 ? (
            <p className="muted">Sin ventas aún.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dataMonto}>
                <XAxis dataKey="name" tickLine={false} axisLine={false} />
                <YAxis
                  tickFormatter={(v) => formatNumber(Number(v), 0)}
                  tickLine={false}
                  axisLine={false}
                  width={54}
                />
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                  formatter={(value) => [formatMoney(Number(value)), "Total"]}
                />
                <Bar dataKey="monto" fill="#e07a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      <section className="card">
        <h3>Actividad en tiempo real</h3>
        {eventos.length === 0 ? (
          <p className="muted">Esperando ventas...</p>
        ) : (
          <ul className="feed">
            {eventos.map((e, i) => (
              <li key={i}>
                <span className="tag">{e.type}</span>
                {e.type === "venta_creada" && (
                  <span>Venta {formatMoney(e.data.total)}</span>
                )}
                {e.type === "venta_anulada" && <span>Venta anulada</span>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
