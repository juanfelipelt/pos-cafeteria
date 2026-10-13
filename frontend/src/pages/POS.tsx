/*
 * POS.tsx — Pantalla del Punto De Venta (POS = Point Of Sale).
 *
 * ¿Qué es?
 *   Es la pantalla que usa el cajero/vendedor para atender a un cliente:
 *   muestra el catálogo de productos, permite elegir cantidades, armar una
 *   "cuenta" (el carrito) y cobrarla.
 *
 * ¿Para qué sirve?
 *   - Listar los productos activos y filtrarlos por categoría.
 *   - Abrir un producto en un modal para escoger la cantidad.
 *   - Administrar el carrito: aumentar, disminuir o quitar ítems.
 *   - Elegir el método de pago y calcular la devuelta en efectivo.
 *   - Enviar la venta al backend con un POST a /ventas.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se monta en la ruta "/pos" (ver App.tsx) y solo es accesible tras
 *     iniciar sesión (lo protege el componente Protected).
 *   - Usa `api` (api.ts) para comunicarse con el backend, que es la misma
 *     API que alimenta a Ventas, Productos, etc.
 *   - Reutiliza `MoneyInput` para capturar valores de dinero y
 *     `formatMoney` para mostrarlos con formato.
 *   - La venta que se crea aquí luego aparece en la pantalla Ventas.tsx.
 */

// Hooks de React que usamos: useEffect (efectos secundarios), useMemo
// (cálculos memorizados) y useState (estado del componente).
import { useEffect, useMemo, useState } from "react";
// Cliente HTTP propio del proyecto para hablar con el backend.
import { api } from "../api";
// Campo de entrada especializado en dinero (evita errores de formato).
import MoneyInput from "../components/MoneyInput";
// Utilidad para mostrar números como moneda (ej: "$1.500").
import { formatMoney } from "../lib/format";

// Forma de una categoría tal como la devuelve el backend.
interface Categoria {
  id: string;
  nombre: string;
}

// Forma de un producto (solo los campos que necesita el POS).
interface Producto {
  id: string;
  nombre: string;
  categoria_id: string | null; // null = "sin categoría"
  imagen: string;
  precio: number;
  stock: number; // unidades disponibles
  estado: boolean; // true = activo, false = inactivo
}

// Un ítem dentro del carrito. Es como una "línea de la cuenta".
// Copiamos los datos del producto para no depender de que siga en la lista.
interface Item {
  producto_id: string;
  nombre: string;
  imagen: string;
  precio: number;
  cantidad: number;
}

// Componente principal de la pantalla POS.
export default function POS() {
  // --- Datos que vienen del backend ---
  const [productos, setProductos] = useState<Producto[]>([]); // catálogo
  const [categorias, setCategorias] = useState<Categoria[]>([]); // filtros
  const [filtro, setFiltro] = useState<string | null>(null); // categoría activa (null = "Todo")

  // --- Estado del carrito / cuenta ---
  const [cart, setCart] = useState<Item[]>([]); // ítems agregados
  const [metodo, setMetodo] = useState("efectivo"); // método de pago elegido
  const [recibido, setRecibido] = useState(0); // efectivo entregado por el cliente
  const [mensaje, setMensaje] = useState(""); // mensaje de éxito
  const [error, setError] = useState(""); // mensaje de error

  // --- Estado de la interfaz (modales) ---
  const [modal, setModal] = useState<Producto | null>(null); // producto abierto en el modal
  const [cantidad, setCantidad] = useState(1); // cantidad elegida en el modal
  const [cartOpen, setCartOpen] = useState(false); // ¿la cuenta se ve en móvil?

  // Trae del backend los productos activos y las categorías al mismo tiempo.
  // Promise.all lanza ambas peticiones en paralelo (más rápido que una por una).
  async function cargar() {
    const [ps, cs] = await Promise.all([
      api<Producto[]>("/productos?solo_activos=true"),
      api<Categoria[]>("/categorias"),
    ]);
    setProductos(ps);
    setCategorias(cs);
  }

  // useEffect con [] = se ejecuta UNA sola vez, al montar la pantalla.
  // Sirve para cargar los datos iniciales.
  useEffect(() => {
    cargar();
  }, []);

  // Si el carrito queda vacío, cerramos el panel de la cuenta.
  // Así no se queda abierto un panel sin nada que mostrar.
  useEffect(() => {
    if (cart.length === 0) setCartOpen(false);
  }, [cart]);

  // useMemo: recalcula la lista visible solo cuando cambian productos o filtro.
  // Si hay un filtro, muestra solo esa categoría; si no, todos los productos.
  const visibles = useMemo(
    () => (filtro ? productos.filter((p) => p.categoria_id === filtro) : productos),
    [productos, filtro]
  );

  // useMemo: suma precio × cantidad de cada ítem para obtener el TOTAL.
  // `reduce` recorre el carrito acumulando el resultado en `s`.
  const total = useMemo(
    () => cart.reduce((s, i) => s + i.precio * i.cantidad, 0),
    [cart]
  );

  // Cuando cambia el total o el método de pago, si es efectivo y aún no se
  // escribió cuánto recibió el cliente, proponemos el total como valor inicial.
  // (Es una comodidad: el caso más común es que paguen con el monto exacto.)
  useEffect(() => {
    if (metodo === "efectivo" && cart.length > 0 && recibido === 0) {
      setRecibido(total);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [total, metodo]);

  // Devuelve el stock disponible de un producto por su id.
  // El operador ?? 0 evita "undefined" si el producto no se encuentra.
  const stockDe = (producto_id: string) =>
    productos.find((p) => p.id === producto_id)?.stock ?? 0;

  // Abre el modal de un producto para elegir cantidad.
  // Si no hay stock, no hace nada (no se puede vender lo agotado).
  function abrir(p: Producto) {
    if (p.stock <= 0) return;
    setModal(p);
    setCantidad(1); // reiniciamos la cantidad a 1 cada vez
  }

  // Agrega al carrito el producto que está abierto en el modal.
  function agregarDesdeModal() {
    if (!modal) return;
    setCart((prev) => {
      // ¿Ya existe ese producto en el carrito?
      const existente = prev.find((i) => i.producto_id === modal.id);
      if (existente) {
        // Sí existe: sumamos la cantidad, sin pasar del stock disponible.
        return prev.map((i) =>
          i.producto_id === modal.id
            ? {
                ...i,
                cantidad: Math.min(i.cantidad + cantidad, modal.stock),
              }
            : i
        );
      }
      // No existe: agregamos un ítem nuevo al final del arreglo.
      return [
        ...prev,
        {
          producto_id: modal.id,
          nombre: modal.nombre,
          imagen: modal.imagen,
          precio: modal.precio,
          cantidad,
        },
      ];
    });
    setModal(null); // cerramos el modal
    setCartOpen(true); // y mostramos la cuenta
  }

  // Aumenta en 1 la cantidad de un ítem, respetando el stock máximo.
  function incrementar(producto_id: string) {
    setCart((prev) =>
      prev.map((i) =>
        i.producto_id === producto_id
          ? { ...i, cantidad: Math.min(i.cantidad + 1, stockDe(producto_id)) }
          : i
      )
    );
  }

  // Disminuye en 1 la cantidad de un ítem y elimina los que llegan a 0.
  function decrementar(producto_id: string) {
    setCart((prev) =>
      prev
        .map((i) =>
          i.producto_id === producto_id
            ? { ...i, cantidad: i.cantidad - 1 }
            : i
        )
        .filter((i) => i.cantidad > 0) // quitamos los de cantidad 0
    );
  }

  // Elimina por completo un producto del carrito.
  function quitar(producto_id: string) {
    setCart((prev) => prev.filter((i) => i.producto_id !== producto_id));
  }

  // Registra la venta en el backend: valida el efectivo, arma el cuerpo del
  // POST y, si todo sale bien, limpia el carrito y recarga el stock.
  async function cobrar() {
    setError("");
    setMensaje("");

    // Si pagan en efectivo pero no alcanza, mostramos error y no continuamos.
    if (metodo === "efectivo" && recibido < total) {
      setError("El efectivo recibido es insuficiente para el total.");
      return;
    }

    // Solo registramos un pago si hay algo que pagar (total > 0).
    const pagos = total > 0 ? [{ monto: total, metodo }] : [];

    try {
      // Enviamos al backend los ítems (producto y cantidad) y los pagos.
      await api("/ventas", {
        method: "POST",
        body: JSON.stringify({
          items: cart.map((i) => ({
            producto_id: i.producto_id,
            cantidad: i.cantidad,
          })),
          pagos,
        }),
      });
      // Éxito: avisamos, vaciamos el carrito y recargamos los productos.
      setMensaje(`Venta registrada por ${formatMoney(total)}`);
      setCart([]);
      setRecibido(0);
      setCartOpen(false);
      await cargar(); // refresca el stock real que devolvió el backend
    } catch (err) {
      // Si el backend responde con error, lo mostramos en pantalla.
      setError(err instanceof Error ? err.message : "Error al cobrar");
    }
  }

  // Encabezado de la cuenta (título + botón de cerrar). Lo guardamos en una
  // variable para reutilizarlo sin duplicar el marcado.
  const cartHead = (
    <div className="cart-head">
      <h3>Cuenta</h3>
      <button
        className="icon-btn cart-close"
        aria-label="Cerrar cuenta"
        onClick={() => setCartOpen(false)}
      >
        <span className="material-symbols-outlined">close</span>
      </button>
    </div>
  );

  // A partir de aquí empieza el marcado (JSX) que se ve en pantalla.
  return (
    <div className="pos">
      <div>
        {/* Chips = botones de filtro por categoría. "Todo" quita el filtro. */}
        <div className="chips">
          <button
            className={filtro === null ? "chip active" : "chip"}
            onClick={() => setFiltro(null)}
          >
            Todo
          </button>
          {/* Un chip por cada categoría que devolvió el backend. */}
          {categorias.map((c) => (
            <button
              key={c.id}
              className={filtro === c.id ? "chip active" : "chip"}
              onClick={() => setFiltro(c.id)}
            >
              {c.nombre}
            </button>
          ))}
        </div>

        {/* Rejilla con las tarjetas de los productos visibles. */}
        <div className="product-grid">
          {visibles.map((p) => (
            <div key={p.id} className="product-card" onClick={() => abrir(p)}>
              {/* Miniatura: si hay imagen la mostramos, si no, un ícono. */}
              <div className="product-thumb">
                {p.imagen ? (
                  <img src={p.imagen} alt={p.nombre} />
                ) : (
                  <span className="material-symbols-outlined">image</span>
                )}
              </div>
              <div className="product-info">
                <span className="name">{p.nombre}</span>
                <span className="price">{formatMoney(p.precio)}</span>
                {/* Etiqueta "Agotado" solo cuando no queda stock. */}
                {p.stock <= 0 && <span className="stock">Agotado</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Panel de la cuenta (carrito). La clase "open" lo muestra en móvil. */}
      <div className={cartOpen ? "card cart open" : "card cart"}>
        {cartHead}
        {cart.length === 0 ? (
          // Carrito vacío: mensaje de ayuda.
          <p className="muted">Agrega productos.</p>
        ) : (
          // Carrito con ítems: tabla con producto, cantidad y subtotal.
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Producto</th>
                <th>Cant.</th>
                <th>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cart.map((i) => (
                <tr key={i.producto_id}>
                  <td>
                    {/* Miniatura del ítem en la cuenta. */}
                    <span className="cart-thumb">
                      {i.imagen ? (
                        <img src={i.imagen} alt={i.nombre} />
                      ) : (
                        <span className="material-symbols-outlined">image</span>
                      )}
                    </span>
                  </td>
                  <td>{i.nombre}</td>
                  <td>
                    {/* Botones − / + para ajustar la cantidad. */}
                    <span className="cart-controls">
                      <button
                        className="ghost"
                        onClick={() => decrementar(i.producto_id)}
                      >
                        −
                      </button>
                      {i.cantidad}
                      <button
                        className="ghost"
                        onClick={() => incrementar(i.producto_id)}
                      >
                        +
                      </button>
                    </span>
                  </td>
                  {/* Subtotal = precio unitario × cantidad. */}
                  <td className="num">{formatMoney(i.precio * i.cantidad)}</td>
                  <td>
                    {/* Botón × para quitar el ítem de la cuenta. */}
                    <button
                      className="ghost small"
                      onClick={() => quitar(i.producto_id)}
                    >
                      ×
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              {/* Fila con el total de toda la cuenta. */}
              <tr className="total-row">
                <td colSpan={3} className="total-label">
                  TOTAL
                </td>
                <td className="total-amount num">
                  {formatMoney(total)}
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        )}

        {/* Sección de pago. */}
        <div className="payment">
          <div className="pay-top">
            <label className="pay-label" htmlFor="metodo-pago">
              Método de pago
            </label>
            {/* Selector de método: efectivo, transferencia o tarjeta. */}
            <select
              id="metodo-pago"
              value={metodo}
              onChange={(e) => setMetodo(e.target.value)}
            >
              <option value="efectivo">Efectivo</option>
              <option value="transferencia">Transferencia</option>
              <option value="tarjeta">Tarjeta</option>
            </select>
          </div>

          {/* Estos campos solo aparecen cuando el pago es en efectivo. */}
          {metodo === "efectivo" && (
            <div className="pay-efectivo">
              <div className="pay-field">
                <label className="pay-label" htmlFor="efectivo-recibido">
                  Recibido
                </label>
                {/* MoneyInput captura cuánto dinero entregó el cliente. */}
                <MoneyInput
                  value={recibido}
                  onChange={setRecibido}
                  placeholder="0"
                />
              </div>
              {/* Caja que muestra "Falta" (rojo) o "Devuelta" (verde). */}
              <div
                className={
                  total > 0 && recibido < total
                    ? "pay-result faltan"
                    : "pay-result devuelta"
                }
              >
                <span className="pay-result-label">
                  {total > 0 && recibido < total ? "Falta" : "Devuelta"}
                </span>
                <strong>
                  {/* Si alcanzó: recibido − total = devuelta.
                      Si no alcanzó: total − recibido = lo que falta. */}
                  {formatMoney(
                    recibido >= total ? recibido - total : total - recibido
                  )}
                </strong>
              </div>
            </div>
          )}

          {/* Botón de cobrar: se deshabilita si no hay ítems o falta efectivo. */}
          <button
            className="primary pay-cobrar"
            disabled={
              cart.length === 0 || (metodo === "efectivo" && recibido < total)
            }
            onClick={cobrar}
          >
            Cobrar · {formatMoney(total)}
          </button>
        </div>
        {/* Mensajes de éxito o error tras intentar cobrar. */}
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </div>

      {/* Barra inferior (útil en móvil): total y botón para ver/cerrar cuenta. */}
      <div className={cart.length === 0 ? "pos-bar hidden" : "pos-bar"}>
        <span className="pos-total">{formatMoney(total)}</span>
        <button onClick={() => setCartOpen((o) => !o)}>
          {cartOpen ? "Cerrar cuenta" : "Ver cuenta"}
        </button>
      </div>

      {/* Modal para elegir la cantidad de un producto antes de agregarlo. */}
      {modal && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          {/* stopPropagation evita que el clic dentro del modal lo cierre. */}
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {/* Imagen grande del producto (o ícono si no tiene). */}
            {modal.imagen ? (
              <img className="thumb-lg" src={modal.imagen} alt={modal.nombre} />
            ) : (
              <div className="thumb-lg product-thumb">
                <span className="material-symbols-outlined">image</span>
              </div>
            )}
            <h3>{modal.nombre}</h3>
            {/* Función autoejecutable: busca el nombre de la categoría del
                producto y lo muestra solo si existe. */}
            {(() => {
              const cat = categorias.find(
                (c) => c.id === modal.categoria_id
              );
              return cat ? <p className="product-cat">{cat.nombre}</p> : null;
            })()}
            <p className="muted">
              {formatMoney(modal.precio)} · stock {modal.stock}
            </p>
            {/* Controles de cantidad, limitados entre 1 y el stock. */}
            <div className="qty-row">
              <button
                className="qty-btn ghost"
                onClick={() => setCantidad((c) => Math.max(1, c - 1))}
              >
                −
              </button>
              <span className="num">{cantidad}</span>
              <button
                className="qty-btn ghost"
                onClick={() => setCantidad((c) => Math.min(modal.stock, c + 1))}
              >
                +
              </button>
            </div>
            <div className="modal-actions">
              <button className="ghost" onClick={() => setModal(null)}>
                Cancelar
              </button>
              {/* Muestra en vivo el subtotal (precio × cantidad). */}
              <button className="primary" onClick={agregarDesdeModal}>
                Agregar · {formatMoney(modal.precio * cantidad)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
