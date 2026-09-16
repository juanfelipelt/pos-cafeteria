import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
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

interface PizarraResumen {
  pendientes: number;
  tareas_pendientes: number;
  notas: number;
}

interface TopProducto {
  producto_id: string;
  nombre: string;
  cantidad: number;
  monto: number;
}

interface Evento {
  type: string;
}

interface PuntoPeriodo {
  periodo: string;
  total: number;
  num_ventas: number;
}

type Rango = "dia" | "semana" | "mes";

const EVENTOS_REFRESH = ["venta_creada", "venta_anulada", "venta_eliminada"];

function pad(n: number, len = 2): string {
  return String(n).padStart(len, "0");
}

function localIso(d: Date): string {
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` +
    `.${pad(d.getMilliseconds(), 3)}`
  );
}

function inicioDia(d: Date): string {
  return localIso(new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0));
}

function finDia(d: Date): string {
  return localIso(
    new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59, 999)
  );
}

function inicioMes(d: Date): string {
  return localIso(new Date(d.getFullYear(), d.getMonth(), 1, 0, 0, 0, 0));
}

function inicioSemana(d: Date): Date {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const dow = (x.getDay() + 6) % 7;
  x.setDate(x.getDate() - dow);
  return x;
}

function paramsActividad(rango: Rango): {
  desde: string;
  hasta: string;
  agrupacion: string;
} {
  const now = new Date();
  const hasta = finDia(now);
  if (rango === "dia") {
    return { desde: inicioDia(now), hasta, agrupacion: "hora" };
  }
  if (rango === "semana") {
    return { desde: localIso(inicioSemana(now)), hasta, agrupacion: "dia" };
  }
  return { desde: inicioMes(now), hasta, agrupacion: "dia" };
}

function construirSerie(
  puntos: PuntoPeriodo[],
  rango: Rango
): { etiqueta: string; total: number }[] {
  const mapa = new Map(puntos.map((p) => [p.periodo, p]));
  const now = new Date();

  if (rango === "dia") {
    return Array.from({ length: 24 }, (_, h) => {
      const key = pad(h);
      return {
        etiqueta: `${key}:00`,
        total: mapa.get(key)?.total ?? 0,
      };
    });
  }

  const inicio =
    rango === "semana"
      ? inicioSemana(now)
      : new Date(now.getFullYear(), now.getMonth(), 1);
  const fin = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const serie: { etiqueta: string; total: number }[] = [];
  for (const d = new Date(inicio); d <= fin; d.setDate(d.getDate() + 1)) {
    const key = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    serie.push({
      etiqueta: `${pad(d.getDate())}/${pad(d.getMonth() + 1)}`,
      total: mapa.get(key)?.total ?? 0,
    });
  }
  return serie;
}

const ETIQUETA_RANGO: Record<Rango, string> = {
  dia: "hoy por hora",
  semana: "esta semana por día",
  mes: "este mes por día",
};

export default function Dashboard() {
  const [resumenHoy, setResumenHoy] = useState<Resumen | null>(null);
  const [resumenMes, setResumenMes] = useState<Resumen | null>(null);
  const [pizarra, setPizarra] = useState<PizarraResumen | null>(null);
  const [top, setTop] = useState<TopProducto[]>([]);
  const [rango, setRango] = useState<Rango>("dia");
  const [actividad, setActividad] = useState<PuntoPeriodo[]>([]);

  const cargarActividad = useCallback(async () => {
    const now = new Date();
    const desdeHoy = inicioDia(now);
    const hastaHoy = finDia(now);
    const desdeMes = inicioMes(now);
    const { desde, hasta, agrupacion } = paramsActividad(rango);
    const [rh, rm, tp, ac, pz] = await Promise.allSettled([
      api<Resumen>(`/reportes/resumen?desde=${desdeHoy}&hasta=${hastaHoy}`),
      api<Resumen>(`/reportes/resumen?desde=${desdeMes}&hasta=${hastaHoy}`),
      api<TopProducto[]>(
        `/reportes/top-productos?desde=${desdeHoy}&hasta=${hastaHoy}&limite=10`
      ),
      api<PuntoPeriodo[]>(
        `/reportes/actividad?desde=${desde}&hasta=${hasta}&agrupacion=${agrupacion}`
      ),
      api<PizarraResumen>("/notas/resumen"),
    ]);
    if (rh.status === "fulfilled") setResumenHoy(rh.value);
    if (rm.status === "fulfilled") setResumenMes(rm.value);
    if (tp.status === "fulfilled") setTop(tp.value);
    if (ac.status === "fulfilled") setActividad(ac.value);
    if (pz.status === "fulfilled") setPizarra(pz.value);
  }, [rango]);

  useEffect(() => {
    cargarActividad();
  }, [cargarActividad]);

  useEffect(() => {
    const es = new EventSource(
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as Evento;
      if (EVENTOS_REFRESH.includes(msg.type) || msg.type.startsWith("nota_")) {
        cargarActividad();
      }
    };
    return () => es.close();
  }, [cargarActividad]);

  const data = top.map((t) => ({ name: t.nombre, vendidos: t.cantidad }));
  const dataMonto = top.map((t) => ({ name: t.nombre, monto: t.monto }));

  const serie = construirSerie(actividad, rango);
  const hayVentas = actividad.length > 0;

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
        <Link to="/pizarra" className="card card-link">
          <span>Pizarra</span>
          <strong>{pizarra?.pendientes ?? 0}</strong>
          <small>{pizarra?.tareas_pendientes ?? 0} tareas pendientes</small>
        </Link>
      </div>

      <div className="grid">
        <section className="card">
          <h3>Más vendidos (cantidad)</h3>
          {data.length === 0 ? (
            <p className="muted">Sin ventas aún.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data}>
                <XAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
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
                <XAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
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
        <div className="card-head">
          <h3>Actividad en tiempo real · {ETIQUETA_RANGO[rango]}</h3>
          <select
            value={rango}
            onChange={(e) => setRango(e.target.value as Rango)}
          >
            <option value="dia">Por día</option>
            <option value="semana">Por semana</option>
            <option value="mes">Por mes</option>
          </select>
        </div>
        {!hayVentas ? (
          <p className="muted">Sin ventas en el período.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={serie}>
              <XAxis
                dataKey="etiqueta"
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                minTickGap={16}
              />
              <YAxis
                tickFormatter={(v) => formatNumber(Number(v), 0)}
                tickLine={false}
                axisLine={false}
                width={60}
              />
              <Tooltip
                cursor={{ fill: "rgba(0,0,0,0.03)" }}
                formatter={(value) => [formatMoney(Number(value)), "Total"]}
              />
              <Bar dataKey="total" fill="#37352f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </div>
  );
}
