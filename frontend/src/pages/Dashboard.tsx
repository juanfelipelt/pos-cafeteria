/*
 * ============================================================================
 * Dashboard.tsx  ·  Página principal con resumen y gráficas
 * ============================================================================
 * ¿Qué es?
 *   La pantalla de inicio ("/") que ve el usuario tras iniciar sesión. Muestra
 *   tarjetas con totales del día/mes, la pizarra y varias gráficas de ventas.
 *
 * ¿Para qué sirve?
 *   - Mostrar cuánto se facturó hoy y en el mes, y cuántas ventas hubo.
 *   - Mostrar cuántas notas/tareas están pendientes en la Pizarra.
 *   - Graficar los productos más vendidos (por cantidad y por dinero).
 *   - Graficar la actividad de ventas en el tiempo (por hora/día).
 *   - Actualizarse automáticamente en tiempo real vía Server-Sent Events (SSE)
 *     cuando se crea/anula/elimina una venta o cambia una nota.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se declara como ruta "/" en `App.tsx`, dentro del `Layout`.
 *   - Usa `api`, `eventSourceUrl`, `getToken` (de `../api`) para los datos.
 *   - Usa `formatMoney` y `formatNumber` (de `../lib/format`) para formatear.
 *   - Usa la librería `recharts` para dibujar las gráficas de barras.
 *   - Los datos vienen de endpoints del backend: "/reportes/...", "/notas/resumen".
 * ============================================================================
 */

// Hooks de React: useCallback (memoriza una función), useEffect y useState.
import { useCallback, useEffect, useState } from "react";
// Link: enlace de react-router que navega sin recargar la página.
import { Link } from "react-router-dom";
// Componentes de la librería de gráficas `recharts`.
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
// Helpers de la API y de formato.
import { api, eventSourceUrl, getToken } from "../api";
import { formatMoney, formatNumber } from "../lib/format";

// Resumen de ventas (total facturado y número de ventas).
interface Resumen {
  total: number;
  num_ventas: number;
}

// Resumen de la Pizarra (notas y tareas pendientes).
interface PizarraResumen {
  pendientes: number;
  tareas_pendientes: number;
  notas: number;
}

// Producto más vendido con su cantidad y monto.
interface TopProducto {
  producto_id: string;
  nombre: string;
  cantidad: number;
  monto: number;
}

// Evento recibido por SSE (solo necesitamos su tipo para filtrar).
interface Evento {
  type: string;
}

// Un punto de la serie de actividad (un período con su total).
interface PuntoPeriodo {
  periodo: string;
  total: number;
  num_ventas: number;
}

// Rango de tiempo que el usuario puede elegir para la gráfica de actividad.
type Rango = "dia" | "semana" | "mes";

// Tipos de evento que, al llegar, hacen recargar el Dashboard.
const EVENTOS_REFRESH = ["venta_creada", "venta_anulada", "venta_eliminada"];

// Rellena un número con ceros a la izquierda (ej: 5 -> "05").
function pad(n: number, len = 2): string {
  return String(n).padStart(len, "0");
}

// Construye una fecha en formato ISO local (sin convertir a UTC) como texto.
// Se usa para mandar fechas al backend en la zona horaria del usuario.
function localIso(d: Date): string {
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` +
    `.${pad(d.getMilliseconds(), 3)}`
  );
}

// Devuelve el instante de inicio del día (00:00:00.000) en formato ISO local.
function inicioDia(d: Date): string {
  return localIso(new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0));
}

// Devuelve el instante de fin del día (23:59:59.999) en formato ISO local.
function finDia(d: Date): string {
  return localIso(
    new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59, 999)
  );
}

// Devuelve el inicio del mes (día 1 a las 00:00) en formato ISO local.
function inicioMes(d: Date): string {
  return localIso(new Date(d.getFullYear(), d.getMonth(), 1, 0, 0, 0, 0));
}

// Devuelve el lunes de la semana a la que pertenece la fecha `d`.
function inicioSemana(d: Date): Date {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  // getDay() da 0=domingo..6=sábado; con (x+6)%7 lo convertimos a 0=lunes..6=domingo.
  const dow = (x.getDay() + 6) % 7;
  // Retrocedemos los días necesarios para llegar al lunes.
  x.setDate(x.getDate() - dow);
  return x;
}

// Según el rango elegido, calcula el rango de fechas y la agrupación a pedir.
function paramsActividad(rango: Rango): {
  desde: string;
  hasta: string;
  agrupacion: string;
} {
  const now = new Date();
  const hasta = finDia(now); // Siempre hasta el final del día actual.
  if (rango === "dia") {
    // Hoy: agrupamos por hora.
    return { desde: inicioDia(now), hasta, agrupacion: "hora" };
  }
  if (rango === "semana") {
    // Esta semana: agrupamos por día.
    return { desde: localIso(inicioSemana(now)), hasta, agrupacion: "dia" };
  }
  // Este mes: agrupamos por día.
  return { desde: inicioMes(now), hasta, agrupacion: "dia" };
}

// Construye la serie completa de puntos para la gráfica de actividad.
// Rellena con 0 los períodos sin ventas para que la barra exista en la gráfica.
function construirSerie(
  puntos: PuntoPeriodo[],
  rango: Rango
): { etiqueta: string; total: number }[] {
  // Mapa periodo -> punto, para búsquedas rápidas.
  const mapa = new Map(puntos.map((p) => [p.periodo, p]));
  const now = new Date();

  if (rango === "dia") {
    // 24 horas del día (00 a 23), cada una con su total (0 si no hubo).
    return Array.from({ length: 24 }, (_, h) => {
      const key = pad(h);
      return {
        etiqueta: `${key}:00`,
        total: mapa.get(key)?.total ?? 0,
      };
    });
  }

  // Para semana/mes: definimos la fecha de inicio y la de hoy.
  const inicio =
    rango === "semana"
      ? inicioSemana(now)
      : new Date(now.getFullYear(), now.getMonth(), 1);
  const fin = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const serie: { etiqueta: string; total: number }[] = [];
  // Recorremos día por día desde el inicio hasta hoy.
  for (const d = new Date(inicio); d <= fin; d.setDate(d.getDate() + 1)) {
    // Clave "YYYY-MM-DD" para buscar el total del backend.
    const key = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    serie.push({
      etiqueta: `${pad(d.getDate())}/${pad(d.getMonth() + 1)}`,
      total: mapa.get(key)?.total ?? 0,
    });
  }
  return serie;
}

// Texto que se muestra junto al título de la gráfica según el rango.
const ETIQUETA_RANGO: Record<Rango, string> = {
  dia: "hoy por hora",
  semana: "esta semana por día",
  mes: "este mes por día",
};

export default function Dashboard() {
  // --- Estados locales con los datos que muestra la pantalla ---
  // Resumen de ventas de HOY.
  const [resumenHoy, setResumenHoy] = useState<Resumen | null>(null);
  // Resumen de ventas de ESTE MES.
  const [resumenMes, setResumenMes] = useState<Resumen | null>(null);
  // Resumen de la Pizarra (pendientes).
  const [pizarra, setPizarra] = useState<PizarraResumen | null>(null);
  // Lista de productos más vendidos hoy.
  const [top, setTop] = useState<TopProducto[]>([]);
  // Rango elegido por el usuario para la gráfica de actividad ("dia" por defecto).
  const [rango, setRango] = useState<Rango>("dia");
  // Puntos de actividad devueltos por el backend (para la gráfica del tiempo).
  const [actividad, setActividad] = useState<PuntoPeriodo[]>([]);

  // Función que pide TODOS los datos del dashboard al backend.
  // Se memoriza con useCallback y se recalcula solo cuando cambia `rango`.
  const cargarActividad = useCallback(async () => {
    const now = new Date();
    // Fechas usadas por varias consultas: hoy y el inicio de mes.
    const desdeHoy = inicioDia(now);
    const hastaHoy = finDia(now);
    const desdeMes = inicioMes(now);
    // Rango/agrupación según lo que el usuario eligió.
    const { desde, hasta, agrupacion } = paramsActividad(rango);
    // Lanzamos las 5 peticiones en paralelo con allSettled, que no se detiene
    // si alguna falla (así una gráfica caída no rompe toda la pantalla).
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
    // Guardamos solo las respuestas que sí llegaron bien ("fulfilled").
    if (rh.status === "fulfilled") setResumenHoy(rh.value);
    if (rm.status === "fulfilled") setResumenMes(rm.value);
    if (tp.status === "fulfilled") setTop(tp.value);
    if (ac.status === "fulfilled") setActividad(ac.value);
    if (pz.status === "fulfilled") setPizarra(pz.value);
  }, [rango]);

  // Carga inicial y cada vez que cambia el rango de la gráfica.
  useEffect(() => {
    cargarActividad();
  }, [cargarActividad]);

  // Suscripción a eventos en tiempo real (SSE): refresca al haber cambios.
  useEffect(() => {
    const es = new EventSource(
      // El token va en la URL porque EventSource no permite cabeceras.
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as Evento;
      // Si el evento es de ventas o de notas, recargamos los datos.
      if (EVENTOS_REFRESH.includes(msg.type) || msg.type.startsWith("nota_")) {
        cargarActividad();
      }
    };
    // Al desmontar, cerramos el canal para liberar la conexión.
    return () => es.close();
  }, [cargarActividad]);

  // Datos para la gráfica de "más vendidos" por CANTIDAD.
  const data = top.map((t) => ({ name: t.nombre, vendidos: t.cantidad }));
  // Datos para la gráfica de "más vendidos" por MONTO ($).
  const dataMonto = top.map((t) => ({ name: t.nombre, monto: t.monto }));

  // Serie completa (con ceros) para la gráfica de actividad.
  const serie = construirSerie(actividad, rango);
  // Sabemos si hay ventas en el período para decidir si mostrar la gráfica.
  const hayVentas = actividad.length > 0;

  // --- Marcado (JSX) de la pantalla ---
  return (
    <div>
      <h2>Dashboard</h2>
      {/* Fila de tarjetas resumen (hoy, mes y pizarra). */}
      <div className="cards">
        {/* Tarjeta: total facturado hoy. Si aún no cargó, mostramos 0. */}
        <div className="card">
          <span>Facturado hoy</span>
          <strong>{formatMoney(resumenHoy?.total ?? 0)}</strong>
          <small>{resumenHoy?.num_ventas ?? 0} ventas</small>
        </div>
        {/* Tarjeta: total facturado en el mes. */}
        <div className="card">
          <span>Facturado este mes</span>
          <strong>{formatMoney(resumenMes?.total ?? 0)}</strong>
          <small>{resumenMes?.num_ventas ?? 0} ventas</small>
        </div>
        {/* Tarjeta enlazada a la Pizarra con las notas pendientes. */}
        <Link to="/pizarra" className="card card-link">
          <span>Pizarra</span>
          <strong>{pizarra?.pendientes ?? 0}</strong>
          <small>{pizarra?.tareas_pendientes ?? 0} tareas pendientes</small>
        </Link>
      </div>

      {/* Rejilla con las dos gráficas de productos más vendidos. */}
      <div className="grid">
        {/* Gráfica 1: más vendidos por CANTIDAD. */}
        <section className="card">
          <h3>Más vendidos (cantidad)</h3>
          {data.length === 0 ? (
            // Si no hay datos, mostramos un mensaje en lugar de una gráfica vacía.
            <p className="muted">Sin ventas aún.</p>
          ) : (
            // ResponsiveContainer hace que la gráfica se adapte al ancho.
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data}>
                {/* Eje X: nombre del producto. */}
                <XAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                {/* Eje Y: unidades vendidas (sin decimales). */}
                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />
                {/* Tooltip: al pasar el mouse muestra el valor formateado. */}
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                  formatter={(value) => [formatNumber(Number(value)), "Unidades"]}
                />
                {/* La barra representa la propiedad "vendidos". */}
                <Bar dataKey="vendidos" fill="#37352f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        {/* Gráfica 2: más vendidos por MONTO ($). */}
        <section className="card">
          <h3>Más vendidos ($)</h3>
          {dataMonto.length === 0 ? (
            <p className="muted">Sin ventas aún.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dataMonto}>
                {/* Eje X: nombre del producto. */}
                <XAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                {/* Eje Y: formateamos los valores como números abreviados. */}
                <YAxis
                  tickFormatter={(v) => formatNumber(Number(v), 0)}
                  tickLine={false}
                  axisLine={false}
                  width={54}
                />
                {/* Tooltip: muestra el monto con formato de dinero. */}
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                  formatter={(value) => [formatMoney(Number(value)), "Total"]}
                />
                {/* La barra representa la propiedad "monto". */}
                <Bar dataKey="monto" fill="#e07a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      {/* Gráfica de actividad en el tiempo, con selector de rango. */}
      <section className="card">
        <div className="card-head">
          {/* El título cambia según el rango elegido (hoy/semana/mes). */}
          <h3>Actividad en tiempo real · {ETIQUETA_RANGO[rango]}</h3>
          {/* Selector que cambia el rango y vuelve a cargar los datos. */}
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
          // Si no hay ventas en el período, avisamos en vez de mostrar la gráfica.
          <p className="muted">Sin ventas en el período.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={serie}>
              {/* Eje X: etiqueta del período (hora o fecha). */}
              <XAxis
                dataKey="etiqueta"
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                minTickGap={16}
              />
              {/* Eje Y: total facturado del período. */}
              <YAxis
                tickFormatter={(v) => formatNumber(Number(v), 0)}
                tickLine={false}
                axisLine={false}
                width={60}
              />
              {/* Tooltip: muestra el total con formato de dinero. */}
              <Tooltip
                cursor={{ fill: "rgba(0,0,0,0.03)" }}
                formatter={(value) => [formatMoney(Number(value)), "Total"]}
              />
              {/* Barra del total facturado en cada período. */}
              <Bar dataKey="total" fill="#37352f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </div>
  );
}
