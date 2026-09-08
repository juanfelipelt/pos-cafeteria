import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { formatMoney } from "../lib/format";

interface Categoria {
  id: string;
  nombre: string;
}

interface Producto {
  id: string;
  nombre: string;
  categoria_id: string | null;
  imagen: string;
  precio: number;
  stock: number;
  estado: boolean;
}

interface Item {
  producto_id: string;
  nombre: string;
  imagen: string;
  precio: number;
  cantidad: number;
}

export default function POS() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [filtro, setFiltro] = useState<string | null>(null);

  const [cart, setCart] = useState<Item[]>([]);
  const [metodo, setMetodo] = useState("efectivo");
  const [monto, setMonto] = useState(0);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  const [modal, setModal] = useState<Producto | null>(null);
  const [cantidad, setCantidad] = useState(1);
  const [cartOpen, setCartOpen] = useState(false);

  async function cargar() {
    const [ps, cs] = await Promise.all([
      api<Producto[]>("/productos?solo_activos=true"),
      api<Categoria[]>("/categorias"),
    ]);
    setProductos(ps);
    setCategorias(cs);
  }

  useEffect(() => {
    cargar();
  }, []);

  useEffect(() => {
    if (cart.length === 0) setCartOpen(false);
  }, [cart]);

  const visibles = useMemo(
    () => (filtro ? productos.filter((p) => p.categoria_id === filtro) : productos),
    [productos, filtro]
  );

  const total = useMemo(
    () => cart.reduce((s, i) => s + i.precio * i.cantidad, 0),
    [cart]
  );

  const stockDe = (producto_id: string) =>
    productos.find((p) => p.id === producto_id)?.stock ?? 0;

  function abrir(p: Producto) {
    if (p.stock <= 0) return;
    setModal(p);
    setCantidad(1);
  }

  function agregarDesdeModal() {
    if (!modal) return;
    setCart((prev) => {
      const existente = prev.find((i) => i.producto_id === modal.id);
      if (existente) {
        return prev.map((i) =>
          i.producto_id === modal.id
            ? {
                ...i,
                cantidad: Math.min(i.cantidad + cantidad, modal.stock),
              }
            : i
        );
      }
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
    setModal(null);
    setCartOpen(true);
  }

  function incrementar(producto_id: string) {
    setCart((prev) =>
      prev.map((i) =>
        i.producto_id === producto_id
          ? { ...i, cantidad: Math.min(i.cantidad + 1, stockDe(producto_id)) }
          : i
      )
    );
  }

  function decrementar(producto_id: string) {
    setCart((prev) =>
      prev
        .map((i) =>
          i.producto_id === producto_id
            ? { ...i, cantidad: i.cantidad - 1 }
            : i
        )
        .filter((i) => i.cantidad > 0)
    );
  }

  function quitar(producto_id: string) {
    setCart((prev) => prev.filter((i) => i.producto_id !== producto_id));
  }

  async function cobrar() {
    setError("");
    setMensaje("");
    const montoFinal = monto > 0 ? monto : total;
    const pagos = montoFinal > 0 ? [{ monto: montoFinal, metodo }] : [];
    try {
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
      setMensaje(`Venta registrada por ${formatMoney(total)}`);
      setCart([]);
      setMonto(0);
      setCartOpen(false);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cobrar");
    }
  }

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

  return (
    <div className="pos">
      <div>
        <div className="chips">
          <button
            className={filtro === null ? "chip active" : "chip"}
            onClick={() => setFiltro(null)}
          >
            Todo
          </button>
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

        <div className="product-grid">
          {visibles.map((p) => (
            <div key={p.id} className="product-card" onClick={() => abrir(p)}>
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
                {p.stock <= 0 && <span className="stock">Agotado</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={cartOpen ? "card cart open" : "card cart"}>
        {cartHead}
        {cart.length === 0 ? (
          <p className="muted">Agrega productos.</p>
        ) : (
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
                  <td>{formatMoney(i.precio * i.cantidad)}</td>
                  <td>
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
          </table>
        )}

        <div className="total">{formatMoney(total)}</div>

        <div className="payment">
          <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="tarjeta">Tarjeta</option>
          </select>
          <MoneyInput
            placeholder="Monto (opcional)"
            value={monto}
            onChange={setMonto}
          />
          <button
            className="primary"
            disabled={cart.length === 0}
            onClick={cobrar}
          >
            Cobrar
          </button>
        </div>
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </div>

      <div className={cart.length === 0 ? "pos-bar hidden" : "pos-bar"}>
        <span className="pos-total">{formatMoney(total)}</span>
        <button onClick={() => setCartOpen((o) => !o)}>
          {cartOpen ? "Cerrar cuenta" : "Ver cuenta"}
        </button>
      </div>

      {modal && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {modal.imagen ? (
              <img className="thumb-lg" src={modal.imagen} alt={modal.nombre} />
            ) : (
              <div className="thumb-lg product-thumb">
                <span className="material-symbols-outlined">image</span>
              </div>
            )}
            <h3>{modal.nombre}</h3>
            <p className="muted">
              {formatMoney(modal.precio)} · stock {modal.stock}
            </p>
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
