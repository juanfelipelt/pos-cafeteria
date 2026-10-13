/*
 * ARCHIVO: src/pages/Compras.tsx
 * -----------------------------------------------------------------------------
 * ¿Qué es?
 *   Esta es la pantalla (página) "Compras" de la aplicación Cafetería POS.
 *   Cafetería POS es el sistema de gestión de una cafetería: aquí se registran las
 *   compras que hace el negocio a sus proveedores.
 *
 * ¿Para qué sirve?
 *   Permite:
 *     - Registrar una compra nueva: elegir proveedor, agregar líneas (productos
 *       terminados o insumos/materia prima) con cantidad y costo, y guardar.
 *     - Editar una compra existente (solo administrador).
 *     - Ver el "Historial de compras" y desplegar el detalle de cada una.
 *     - Anular o eliminar compras (solo administrador). Estas acciones revierten
 *       el stock que la compra había sumado.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se monta como ruta "/compras" dentro de <App /> (App.tsx), protegida por
 *     login y envuelta por <Layout />.
 *   - Usa {api} (src/api.ts) para hablar con el backend (FastAPI). Cada llamada
 *     lleva el token guardado en localStorage.
 *   - Usa {useAuth} (src/auth.tsx) para saber el rol del usuario: muchas acciones
 *     solo se muestran si el rol es "admin".
 *   - Usa <MoneyInput /> (componente reutilizable) para escribir costos con
 *     formato de moneda, y {formatMoney} (src/lib/format.ts) para mostrarlos.
 *   - Se alimenta de los datos de Proveedores, Productos e Insumos, que son
 *     otras páginas del mismo sistema.
 * -----------------------------------------------------------------------------
 */

// --- Importaciones -----------------------------------------------------------
import { Fragment, useEffect, useState } from "react"; // Hooks de React: estado, efectos y agrupar elementos sin crear nodo extra (Fragment).
import { api } from "../api"; // Cliente HTTP central: agrega el token y arma las peticiones al backend.
import MoneyInput from "../components/MoneyInput"; // Campo de texto especializado para escribir valores de dinero.
import { useAuth } from "../auth"; // Hook que entrega el usuario autenticado (para permisos por rol).
import { formatMoney } from "../lib/format"; // Función que convierte un número en texto con formato de moneda.

// --- Tipos (interfaces) de los datos que maneja la pantalla ------------------
// Ayudan a TypeScript a avisarnos si usamos mal un dato.

// Proveedor: sólo necesitamos su id y su nombre para el desplegable y el historial.
interface Proveedor {
  id: string;
  nombre: string;
}

// Producto terminado (lo que se vende en la cafetería). Aquí sólo usamos id y nombre.
interface Producto {
  id: string;
  nombre: string;
}

// Insumo (materia prima, ej. café molido). Además del nombre lleva su unidad de medida.
interface Insumo {
  id: string;
  nombre: string;
  unidad: string;
}

// Una línea (renglón) de la compra que estamos armando en el formulario.
// "tipo" indica si la línea es un producto o un insumo; "ref_id" apunta al
// registro elegido; "precio_unitario" es el costo de una unidad.
interface ItemCompra {
  tipo: "producto" | "insumo";
  ref_id: string;
  nombre: string;
  unidad: string;
  cantidad: number;
  precio_unitario: number;
}

// Una línea del detalle tal como la devuelve el backend al consultar compras.
// Los campos con "?" son opcionales porque dependiendo del tipo de línea unos
// vienen y otros no (ej. nombre_insumo sólo en líneas de insumo).
interface DetalleCompra {
  id: string;
  tipo: string;
  nombre: string;
  nombre_producto?: string;
  nombre_insumo?: string;
  producto_id?: string | null;
  insumo_id?: string | null;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

// Una compra ya guardada en el sistema (como la devuelve el backend).
interface Compra {
  id: string;
  proveedor_id: string;
  fecha: string;
  detalles: DetalleCompra[];
  total: number;
  anulada: boolean;
}

// Componente principal de la página. React lo renderiza cuando el usuario entra a "/compras".
export default function Compras() {
  const { user } = useAuth(); // Usuario logueado; se usa para mostrar acciones sólo a "admin".

  // --- Estados que guardan las LISTAS de datos traídas del backend ---
  const [proveedores, setProveedores] = useState<Proveedor[]>([]); // Lista de proveedores disponibles.
  const [productos, setProductos] = useState<Producto[]>([]); // Lista de productos terminados.
  const [insumos, setInsumos] = useState<Insumo[]>([]); // Lista de insumos activos.
  const [compras, setCompras] = useState<Compra[]>([]); // Historial de compras registradas.

  // --- Estados del FORMULARIO de registro/edición de una compra ---
  const [proveedorId, setProveedorId] = useState(""); // Proveedor elegido para esta compra.
  const [items, setItems] = useState<ItemCompra[]>([]); // Líneas (productos/insumos) que va armando el usuario.
  const [tipoLinea, setTipoLinea] = useState<"producto" | "insumo">("producto"); // Indica si la próxima línea será producto o insumo.
  const [refId, setRefId] = useState(""); // Id del producto o insumo seleccionado en la línea actual.
  const [cantidad, setCantidad] = useState(""); // Cantidad escrita (texto) para la línea actual.
  const [precio, setPrecio] = useState(0); // Costo unitario de la línea actual (número, viene de MoneyInput).

  // --- Estados de control de la interfaz ---
  const [abierta, setAbierta] = useState<string | null>(null); // Id de la compra cuyo detalle está desplegado (o null si ninguna).
  const [editandoCompraId, setEditandoCompraId] = useState<string | null>(null); // Si tiene id, el formulario está editando esa compra; si es null, está creando una nueva.
  const [mensaje, setMensaje] = useState(""); // Mensaje de éxito para mostrar al usuario.
  const [error, setError] = useState(""); // Mensaje de error para mostrar al usuario.

  // Trae del backend, en paralelo, todo lo que la pantalla necesita para funcionar.
  async function cargar() {
    // Promise.all lanza las 4 peticiones al mismo tiempo (más rápido que una por una).
    const [provs, prods, ins, comps] = await Promise.all([
      api<Proveedor[]>("/proveedores"), // Proveedores para el desplegable.
      api<Producto[]>("/productos"), // Productos para el desplegable.
      api<Insumo[]>("/insumos?solo_activos=true"), // Sólo insumos activos (los inactivos no se pueden comprar).
      api<Compra[]>("/compras"), // Historial de compras.
    ]);
    // Guardamos cada resultado en su estado para que React vuelva a dibujar la pantalla.
    setProveedores(provs);
    setProductos(prods);
    setInsumos(ins);
    setCompras(comps);
  }

  // useEffect con arreglo vacío [] = se ejecuta UNA sola vez, al montar la página.
  useEffect(() => {
    cargar();
  }, []);

  // Agrega la línea actual (según tipoLinea) a la lista "items" del formulario.
  function agregarItem() {
    // Validación mínima: sin referencia ni cantidad no hay nada que agregar.
    if (!refId || !cantidad) return;
    if (tipoLinea === "producto") {
      // Buscamos el producto elegido en la lista para conocer su nombre.
      const p = productos.find((x) => x.id === refId);
      if (!p) return; // Si no existe, no hacemos nada.
      // Agregamos una nueva línea al final, sin mutar el arreglo anterior (patrón inmutable de React).
      setItems((prev) => [
        ...prev,
        {
          tipo: "producto",
          ref_id: p.id,
          nombre: p.nombre,
          unidad: "", // Los productos terminados no usan unidad de medida.
          cantidad: Number(cantidad), // Convertimos el texto a número.
          precio_unitario: precio,
        },
      ]);
    } else {
      // Igual que arriba, pero para insumos (que sí tienen unidad).
      const i = insumos.find((x) => x.id === refId);
      if (!i) return;
      setItems((prev) => [
        ...prev,
        {
          tipo: "insumo",
          ref_id: i.id,
          nombre: i.nombre,
          unidad: i.unidad,
          cantidad: Number(cantidad),
          precio_unitario: precio,
        },
      ]);
    }
    // Limpiamos los campos de la línea para dejar listo el formulario para la siguiente.
    setRefId("");
    setCantidad("");
    setPrecio(0);
  }

  // Actualiza un campo (cantidad o costo) de una línea ya agregada, identificada por su posición "idx".
  function actualizarItem(
    idx: number,
    campo: "cantidad" | "precio_unitario",
    valor: number
  ) {
    // Recorremos todas las líneas y sólo cambiamos la que está en la posición idx.
    setItems((prev) =>
      prev.map((it, i) => (i === idx ? { ...it, [campo]: valor } : it))
    );
  }

  // Elimina la línea de la posición indicada.
  function quitarItem(idx: number) {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  }

  // Carga una compra existente en el formulario para poder editarla.
  function editarCompra(c: Compra) {
    setEditandoCompraId(c.id); // Marcamos que estamos en modo edición.
    setProveedorId(c.proveedor_id); // Preseleccionamos el proveedor de esa compra.
    // Convertimos el detalle que devuelve el backend al formato de líneas del formulario.
    setItems(
      c.detalles.map((d) => {
        const tipo = d.tipo === "insumo" ? "insumo" : "producto";
        const ref_id =
          tipo === "insumo" ? d.insumo_id ?? "" : d.producto_id ?? "";
        // El nombre puede venir en distintos campos según la versión del backend; usamos el primero disponible.
        const nombre =
          d.nombre || d.nombre_producto || d.nombre_insumo || "—";
        // Para insumos buscamos su unidad en la lista cargada; los productos no tienen unidad.
        const unidad =
          tipo === "insumo"
            ? insumos.find((i) => i.id === d.insumo_id)?.unidad ?? ""
            : "";
        return {
          tipo,
          ref_id,
          nombre,
          unidad,
          cantidad: d.cantidad,
          precio_unitario: d.precio_unitario,
        };
      })
    );
    // Limpiamos mensajes previos.
    setMensaje("");
    setError("");
    // Subimos al inicio de la página para que el usuario vea el formulario con los datos cargados.
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Sale del modo edición y deja el formulario vacío.
  function cancelarEdicion() {
    setEditandoCompraId(null); // Volvemos a modo "crear".
    setItems([]); // Sin líneas.
    setProveedorId(""); // Sin proveedor elegido.
    setMensaje("");
  }

  // Envía al backend la compra (nueva o editada según editandoCompraId).
  async function guardar() {
    setError("");
    setMensaje("");
    // Armamos el "payload" (los datos que viajan al servidor) en el formato que éste espera.
    const payload = {
      proveedor_id: proveedorId,
      items: items.map((i) => ({
        tipo: i.tipo,
        // Enviamos el id en el campo correcto según el tipo; el otro va en null.
        producto_id: i.tipo === "producto" ? i.ref_id : null,
        insumo_id: i.tipo === "insumo" ? i.ref_id : null,
        cantidad: i.cantidad,
        precio_unitario: i.precio_unitario,
      })),
    };
    try {
      if (editandoCompraId) {
        // Si estamos editando, actualizamos la compra existente (PUT).
        await api(`/compras/${editandoCompraId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setMensaje("Compra actualizada.");
      } else {
        // Si no, creamos una compra nueva (POST).
        await api("/compras", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setMensaje("Compra registrada.");
      }
      // Tras guardar: limpiamos el formulario, salimos de edición y recargamos el historial.
      setItems([]);
      setProveedorId("");
      setEditandoCompraId(null);
      await cargar();
    } catch (err) {
      // Si algo falla, mostramos el mensaje de error (o "Error" genérico).
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Anula una compra (revierte su efecto en el stock), previa confirmación del usuario.
  async function anular(id: string) {
    if (!window.confirm("¿Anular esta compra? Se revertirá el stock.")) return;
    setError("");
    try {
      await api(`/compras/${id}/anular`, { method: "POST" }); // Endpoint especial de anulación.
      await cargar(); // Refrescamos el historial.
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Elimina definitivamente una compra (también revierte stock), previa confirmación.
  async function eliminar(id: string) {
    if (
      !window.confirm("¿Estás seguro de eliminar esta compra? Se revertirá el stock.")
    )
      return;
    setError("");
    try {
      await api(`/compras/${id}`, { method: "DELETE" }); // Método DELETE.
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // --- Datos derivados (se recalculan en cada render, no son estados) ---
  // Total de la compra que se está armando: suma de cantidad × costo de cada línea.
  const total = items.reduce((s, i) => s + i.cantidad * i.precio_unitario, 0);
  // Convierte un id de proveedor en su nombre legible (o "—" si no se encuentra).
  const nombreProveedor = (id: string) =>
    proveedores.find((p) => p.id === id)?.nombre ?? "—";
  // Obtiene el nombre más adecuado de una línea del detalle del historial.
  const nombreDetalle = (d: DetalleCompra) =>
    d.nombre ?? d.nombre_producto ?? d.nombre_insumo ?? "—";

  // --- Render de la pantalla (JSX) -------------------------------------------
  return (
    <div>
      <h2>Compras</h2>

      {/* Mensaje de error general, sólo se muestra si hay texto */}
      {error && <p className="error">{error}</p>}

      {/* Tarjeta con el formulario de registro/edición */}
      <section className="card">
        {/* El título cambia según si estamos editando o creando */}
        <h3>{editandoCompraId ? "Editar compra" : "Registrar compra"}</h3>
        <label>
          Proveedor
          {/* Desplegable con todos los proveedores; al elegir uno se guarda en proveedorId */}
          <select
            value={proveedorId}
            onChange={(e) => setProveedorId(e.target.value)}
          >
            <option value="">Seleccionar...</option>
            {proveedores.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
        </label>

        {/* Botones tipo "chip" para escoger si la línea será un producto o un insumo */}
        <div className="chips" style={{ marginTop: 12 }}>
          <button
            className={tipoLinea === "producto" ? "chip active" : "chip"}
            onClick={() => {
              setTipoLinea("producto");
              setRefId(""); // Al cambiar de tipo, limpiamos la selección anterior.
            }}
          >
            Producto terminado
          </button>
          <button
            className={tipoLinea === "insumo" ? "chip active" : "chip"}
            onClick={() => {
              setTipoLinea("insumo");
              setRefId("");
            }}
          >
            Insumo (materia prima)
          </button>
        </div>

        {/* Fila para agregar una línea: seleccionar ítem, cantidad y costo */}
        <div className="inline-form" style={{ marginTop: 10 }}>
          {/* El desplegable cambia su contenido según el tipo elegido (productos o insumos) */}
          <select value={refId} onChange={(e) => setRefId(e.target.value)}>
            <option value="">
              {tipoLinea === "producto" ? "Producto..." : "Insumo..."}
            </option>
            {tipoLinea === "producto"
              ? productos.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))
              : insumos.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nombre} ({i.unidad})
                  </option>
                ))}
          </select>
          <input
            type="number"
            step="any"
            placeholder="Cantidad"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
          />
          {/* MoneyInput se encarga de dar formato mientras se escribe el costo */}
          <MoneyInput
            placeholder="Costo unitario"
            value={precio}
            onChange={setPrecio}
          />
          <button type="button" onClick={agregarItem}>
            Agregar
          </button>
        </div>

        {/* La tabla de líneas sólo aparece cuando ya hay al menos una agregada */}
        {items.length > 0 && (
          <table style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Nombre</th>
                <th>Cant.</th>
                <th>Costo</th>
                <th>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {/* Recorremos cada línea del formulario; "idx" es su posición para editarla o quitarla */}
              {items.map((i, idx) => (
                <tr key={idx}>
                  <td data-label="Tipo">{i.tipo}</td>
                  <td data-label="Nombre" className="cell-main">
                    {i.nombre}
                    {/* Mostramos la unidad entre paréntesis sólo si existe */}
                    {i.unidad ? ` (${i.unidad})` : ""}
                  </td>
                  <td data-label="Cant.">
                    {/* Editar la cantidad recalcula el subtotal automáticamente */}
                    <input
                      type="number"
                      step="any"
                      className="qty-input"
                      value={i.cantidad}
                      onChange={(e) =>
                        actualizarItem(idx, "cantidad", Number(e.target.value))
                      }
                    />
                  </td>
                  <td data-label="Costo">
                    {/* Editar el costo también recalcula el subtotal */}
                    <MoneyInput
                      value={i.precio_unitario}
                      onChange={(v) => actualizarItem(idx, "precio_unitario", v)}
                    />
                  </td>
                  <td data-label="Subtotal">
                    {/* Subtotal = cantidad × costo unitario, mostrado con formato de moneda */}
                    {formatMoney(i.cantidad * i.precio_unitario)}
                  </td>
                  <td className="no-label">
                    <button
                      className="ghost danger"
                      onClick={() => quitarItem(idx)}
                    >
                      Quitar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Total general de todas las líneas */}
        <div className="total">{formatMoney(total)}</div>

        <div className="inline-form" style={{ marginTop: 4 }}>
          {/* El botón de guardar se deshabilita si falta proveedor o si no hay líneas */}
          <button
            className="primary"
            disabled={!proveedorId || items.length === 0}
            onClick={guardar}
          >
            {editandoCompraId ? "Guardar cambios" : "Guardar compra"}
          </button>
          {/* El botón Cancelar sólo aparece cuando estamos editando */}
          {editandoCompraId && (
            <button className="ghost" onClick={cancelarEdicion}>
              Cancelar
            </button>
          )}
        </div>
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      {/* Tarjeta con el historial de compras ya registradas */}
      <section className="card">
        <h3>Historial de compras</h3>
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Proveedor</th>
              <th>Total</th>
              <th>Estado</th>
              {/* La columna de acciones sólo se muestra a administradores */}
              {user?.rol === "admin" && <th></th>}
            </tr>
          </thead>
          <tbody>
            {/* Por cada compra dibujamos una fila; Fragment permite agrupar la fila y su detalle sin nodo extra */}
            {compras.map((c) => (
              <Fragment key={c.id}>
                <tr
                  className="venta-row"
                  // Al hacer clic, abrimos/cerramos el detalle de esa compra (toggle)
                  onClick={() => setAbierta(abierta === c.id ? null : c.id)}
                >
                  <td data-label="Fecha">
                    {/* Convertimos la fecha ISO a texto legible con día, mes, año, hora y minuto */}
                    {new Date(c.fecha).toLocaleString(undefined, {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td data-label="Proveedor">{nombreProveedor(c.proveedor_id)}</td>
                  <td data-label="Total">{formatMoney(c.total)}</td>
                  <td data-label="Estado">
                    {/* La "píldora" cambia de color según si la compra está anulada */}
                    <span className={c.anulada ? "pill off" : "pill on"}>
                      {c.anulada ? "Anulada" : "Registrada"}
                    </span>
                  </td>
                  {/* Celda de acciones sólo para admin */}
                  {user?.rol === "admin" && (
                    <td
                      className="no-label"
                      // stopPropagation evita que al pulsar un botón se dispare también el toggle de la fila
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="actions">
                        {/* Editar y Anular sólo tienen sentido si la compra no está anulada */}
                        {!c.anulada && (
                          <>
                            <button
                              className="ghost"
                              onClick={() => editarCompra(c)}
                            >
                              Editar
                            </button>
                            <button
                              className="ghost"
                              onClick={() => anular(c.id)}
                            >
                              Anular
                            </button>
                          </>
                        )}
                        {/* Eliminar está siempre disponible para admin */}
                        <button
                          className="ghost danger"
                          onClick={() => eliminar(c.id)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
                {/* Fila extra con el detalle; sólo se dibuja si esta compra es la "abierta" */}
                {abierta === c.id && (
                  <tr className="detalle-row">
                    {/* colSpan hace que la celda ocupe todas las columnas (5 si admin, 4 si no) */}
                    <td colSpan={user?.rol === "admin" ? 5 : 4}>
                      <div className="detail-panel">
                        {/* Listamos cada línea del detalle: nombre × cantidad y su subtotal */}
                        {c.detalles.map((d) => (
                          <div
                            key={d.id}
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              padding: "3px 0",
                            }}
                          >
                            <span>
                              {nombreDetalle(d)} × {d.cantidad}
                            </span>
                            <span>{formatMoney(d.subtotal)}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
