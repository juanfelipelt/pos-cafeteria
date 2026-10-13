/*
 * ============================================================================
 * PÁGINA: Costeo
 * ============================================================================
 * ¿Qué es este archivo?
 *   Es el componente React de la pantalla "Costeo". Muestra cuánto dinero
 *   entra (ventas del día), cuánto cuesta producir/vender (costo variable)
 *   y cuánto pesan los gastos que se pagan sin importar si vendes o no
 *   (costos fijos: arriendo, servicios, sueldos, etc.).
 *
 * ¿Para qué sirve?
 *   Ayuda al administrador a saber si el negocio está ganando o perdiendo
 *   y cuánto necesita vender para no perder dinero (punto de equilibrio).
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Usa `api` (../api) para pedirle datos al backend: el resumen del día,
 *     el margen de cada producto y la lista de costos fijos.
 *   - Usa `useAuth` (../auth) para saber quién es el usuario y su rol; si no
 *     es administrador, lo redirige al inicio.
 *   - Usa `MoneyInput` para capturar montos con formato de dinero.
 *   - Usa `formatMoney`/`formatNumber` (../lib/format) para mostrar los
 *     valores bonitos (con $ y separadores de miles).
 *   - Las páginas Reportes y Configuración (días laborables) influyen en los
 *     cálculos que se muestran aquí.
 * ============================================================================
 */

import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney, formatNumber } from "../lib/format";

// ---------------------------------------------------------------------------
// Tipos de datos (interfaces) que devuelve el backend.
// TypeScript las usa para saber qué campos trae cada objeto y evitar errores.
// ---------------------------------------------------------------------------

// Resumen financiero del período (normalmente un día) que calcula el backend.
interface Resumen {
  ventas: number; // Total vendido en el período.
  costo_variable: number; // Costo de los insumos de lo vendido (varía con las ventas).
  margen: number; // ventas - costo_variable (lo que aporta la venta).
  margen_pct: number; // Ese margen expresado en porcentaje.
  costos_fijos_mes: number; // Suma de todos los costos fijos activos del mes.
  dias_laborables_mes: number; // Cuántos días se trabaja al mes (de Configuración).
  dias_laborables_rango: number; // Días laborables dentro del rango consultado.
  costo_fijo_diario: number; // Costo fijo del mes repartido en los días laborables.
  costo_fijo_periodo: number; // Costo fijo que toca al período consultado.
  utilidad: number; // margen - costo_fijo_periodo (ganancia real).
  punto_equilibrio: number | null; // Cuánto hay que vender para no perder (null si no aplica).
  faltante_equilibrio: number | null; // Cuánto falta para llegar al equilibrio.
}

// Margen de contribución de un producto: cuánto deja cada venta de ese producto.
interface Margen {
  producto_id: string; // Identificador único del producto.
  nombre: string; // Nombre para mostrar al usuario.
  tipo: string; // Categoría del producto (bebida, comida, etc.).
  precio: number; // Precio de venta.
  costo: number; // Cuánto cuesta producirlo.
  margen: number; // precio - costo.
  margen_pct: number; // margen como porcentaje del precio.
  punto_equilibrio_unidades: number | null; // Cuántas unidades hay que vender para cubrir costos.
}

// Un gasto fijo mensual configurable por el administrador.
interface CostoFijo {
  id: string; // Identificador único.
  nombre: string; // Ej: "Arriendo", "Internet".
  monto: number; // Valor mensual del gasto.
  activo: boolean; // Si está activo cuenta para el cálculo; si no, se ignora.
}

// Devuelve la fecha de hoy en formato ISO "AAAA-MM-DD", que es el formato
// que entienden los <input type="date"> y el backend. Se construye a mano
// (en vez de toISOString) para usar la fecha LOCAL del computador y evitar
// desfases por zona horaria.
function hoyIso(): string {
  const d = new Date();
  // Ayudante que agrega un cero a la izquierda: 5 -> "05".
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// Componente principal de la página. `export default` permite importarlo
// como `import Costeo from "../pages/Costeo"` desde el enrutador.
export default function Costeo() {
  // `user` es el usuario que inició sesión (o null si no hay sesión).
  const { user } = useAuth();
  // Bandera derivada: true solo si el usuario es administrador.
  const esAdmin = user?.rol === "admin";

  // ------------------------------ ESTADO ---------------------------------
  // Cada useState guarda un dato que, cuando cambia, hace que la pantalla
  // se vuelva a dibujar automáticamente con la información actualizada.

  // Fecha seleccionada en el calendario; arranca con la fecha de hoy.
  const [fecha, setFecha] = useState(hoyIso());
  // Resumen financiero del día (null mientras no ha cargado).
  const [resumen, setResumen] = useState<Resumen | null>(null);
  // Lista de productos con su margen.
  const [margenes, setMargenes] = useState<Margen[]>([]);
  // Lista de costos fijos configurados.
  const [costos, setCostos] = useState<CostoFijo[]>([]);

  // Campos del formulario para CREAR un nuevo costo fijo.
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevoMonto, setNuevoMonto] = useState(0);
  // Costo que se está editando en el modal (null si el modal está cerrado).
  const [editando, setEditando] = useState<CostoFijo | null>(null);
  // Mensaje de error a mostrar, por ejemplo si falla una petición.
  const [error, setError] = useState("");

  // ---------------------------- PETICIÓN API -----------------------------
  // Pide al backend, EN PARALELO, el resumen del día, los márgenes y los
  // costos fijos, y guarda las tres respuestas en el estado.
  async function cargar() {
    // Armamos el rango que cubre TODO el día seleccionado (de 00:00 a 23:59).
    const desde = `${fecha}T00:00:00`;
    const hasta = `${fecha}T23:59:59.999`;
    // Promise.all espera a que las tres peticiones terminen a la vez
    // (más rápido que pedirlas una detrás de otra).
    const [res, marg, cos] = await Promise.all([
      api<Resumen>(`/costeo/resumen?desde=${desde}&hasta=${hasta}`),
      api<Margen[]>("/costeo/productos"),
      api<CostoFijo[]>("/costos-fijos"),
    ]);
    setResumen(res);
    setMargenes(marg);
    setCostos(cos);
  }

  // EFECTO: cada vez que cambie la fecha o el rol, vuelve a pedir los datos.
  useEffect(() => {
    // Si no es administrador, no consultamos nada.
    if (!esAdmin) return;
    cargar().catch((err) =>
      setError(err instanceof Error ? err.message : "Error")
    );
    // Desactivamos el aviso de ESLint: `cargar` usa `fecha`, que ya está
    // en la lista de dependencias, así que no hace falta incluirla aparte.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fecha, esAdmin]);

  // GUARDA DE SEGURIDAD: si alguien que no es admin entra a esta ruta,
  // lo enviamos al inicio ("/") reemplazando la entrada del historial.
  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  // ------------------------ CRUD DE COSTOS FIJOS -------------------------

  // Maneja el formulario "Nuevo costo fijo": crea el registro en el backend.
  async function crearCosto(e: React.FormEvent) {
    e.preventDefault(); // Evita que el navegador recargue la página.
    setError("");
    try {
      await api("/costos-fijos", {
        method: "POST",
        body: JSON.stringify({ nombre: nuevoNombre, monto: nuevoMonto }),
      });
      // Limpiamos el formulario tras crear.
      setNuevoNombre("");
      setNuevoMonto(0);
      // Recargamos para ver el nuevo costo en la tabla.
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Guarda los cambios del costo que se está editando (botón "Guardar" del modal).
  async function guardarCosto() {
    if (!editando) return; // Si no hay nada en edición, no hacemos nada.
    await api(`/costos-fijos/${editando.id}`, {
      method: "PUT", // PUT = actualizar un registro existente.
      body: JSON.stringify({
        nombre: editando.nombre,
        monto: editando.monto,
        activo: editando.activo,
      }),
    });
    setEditando(null); // Cerramos el modal.
    await cargar(); // Refrescamos la tabla.
  }

  // Elimina un costo fijo, pidiendo confirmación antes por seguridad.
  async function eliminarCosto(id: string) {
    if (!window.confirm("¿Eliminar este costo fijo?")) return;
    await api(`/costos-fijos/${id}`, { method: "DELETE" });
    await cargar();
  }

  // Devuelve una clase CSS verde ("ok") si el número es >= 0, o roja
  // ("error") si es negativo. Se usa para pintar ganancias y pérdidas.
  const positivo = (n: number) => (n >= 0 ? "ok" : "error");

  return (
    <div>
      {/* Encabezado de la página: título + selector de fecha (calendario). */}
      <div className="card-head">
        <h2 style={{ margin: 0 }}>Costeo</h2>
        {/* Al cambiar la fecha, el useEffect de arriba vuelve a consultar. */}
        <input
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
        />
      </div>

      {/* Si hay un error guardado en el estado, lo mostramos en rojo. */}
      {error && <p className="error">{error}</p>}

      {/* Tarjetas resumen: solo se dibujan si ya llegaron los datos (resumen != null). */}
      {resumen && (
        <div className="cards">
          {/* Tarjeta 1: ventas y margen del día. */}
          <div className="card">
            <span>Ventas del día</span>
            <strong>{formatMoney(resumen.ventas)}</strong>
            <small>
              Margen {formatMoney(resumen.margen)} ({formatNumber(resumen.margen_pct, 1)}%)
            </small>
          </div>
          {/* Tarjeta 2: porción diaria de los costos fijos. */}
          <div className="card">
            <span>Costo fijo del día</span>
            <strong>{formatMoney(resumen.costo_fijo_diario)}</strong>
            <small>
              {formatMoney(resumen.costos_fijos_mes)}/mes ÷ {resumen.dias_laborables_mes} días
            </small>
          </div>
          {/* Tarjeta 3: utilidad (verde si es positiva, roja si es negativa). */}
          <div className="card">
            <span>Utilidad del día</span>
            <strong className={positivo(resumen.utilidad)}>
              {formatMoney(resumen.utilidad)}
            </strong>
            <small>Costo variable {formatMoney(resumen.costo_variable)}</small>
          </div>
          {/* Tarjeta 4: cuánto falta para no perder dinero. */}
          <div className="card">
            <span>Punto de equilibrio</span>
            <strong>
              {resumen.punto_equilibrio === null
                ? "—" // null => no se puede calcular todavía.
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

      {/* Tabla: cuánto deja (margen) cada producto. */}
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
            {/* Recorremos los productos y creamos una fila por cada uno. */}
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
            {/* Si no hay productos, mostramos una fila con mensaje. */}
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

      {/* Zona de administración: solo visible para el rol "admin". */}
      {esAdmin && (
        <>
          {/* Formulario para crear un costo fijo nuevo. */}
          <form onSubmit={crearCosto} className="card">
            <h3>Nuevo costo fijo (mensual)</h3>
            <div className="inline-form">
              <input
                placeholder="Nombre (ej. Arriendo)"
                value={nuevoNombre}
                onChange={(e) => setNuevoNombre(e.target.value)}
                required
              />
              {/* MoneyInput formatea el monto mientras se escribe. */}
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

          {/* Tabla con los costos fijos ya registrados. */}
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
                {/* Una fila por cada costo fijo. */}
                {costos.map((c) => (
                  <tr key={c.id}>
                    <td data-label="Nombre" className="cell-main">
                      {c.nombre}
                    </td>
                    <td data-label="Monto">{formatMoney(c.monto)}</td>
                    <td data-label="Estado">
                      {/* Etiqueta verde si está activo, gris si no. */}
                      <span className={c.activo ? "pill on" : "pill off"}>
                        {c.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="no-label">
                      <div className="actions">
                        {/* "Editar" abre el modal cargando este costo. */}
                        <button className="ghost" onClick={() => setEditando(c)}>
                          Editar
                        </button>
                        {/* "Eliminar" borra el costo (con confirmación). */}
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
                {/* Mensaje cuando todavía no hay costos fijos. */}
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

      {/* MODAL de edición: solo se renderiza si `editando` tiene un valor. */}
      {editando && (
        // Al hacer clic en el fondo oscuro se cierra el modal.
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          {/* stopPropagation evita que un clic DENTRO del modal lo cierre. */}
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar costo fijo</h3>
            <div
              className="inline-form"
              style={{ flexDirection: "column", alignItems: "stretch" }}
            >
              {/* Editar el nombre: copiamos el objeto y cambiamos solo ese campo. */}
              <input
                placeholder="Nombre"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
              {/* Editar el monto mensual. */}
              <MoneyInput
                placeholder="Monto mensual"
                value={editando.monto}
                onChange={(v) => setEditando({ ...editando, monto: v })}
              />
              {/* Casilla para activar o desactivar el costo. */}
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
            {/* Botones del modal: cancelar o guardar los cambios. */}
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
