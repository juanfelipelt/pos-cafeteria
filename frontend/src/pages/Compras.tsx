import { Fragment, useEffect, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney } from "../lib/format";

interface Proveedor {
  id: string;
  nombre: string;
}

interface Producto {
  id: string;
  nombre: string;
}

interface ItemCompra {
  producto_id: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
}

interface DetalleCompra {
  id: string;
  producto_id: string;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

interface Compra {
  id: string;
  proveedor_id: string;
  fecha: string;
  detalles: DetalleCompra[];
  total: number;
  anulada: boolean;
}

export default function Compras() {
  const { user } = useAuth();
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [compras, setCompras] = useState<Compra[]>([]);

  const [proveedorId, setProveedorId] = useState("");
  const [items, setItems] = useState<ItemCompra[]>([]);
  const [productoId, setProductoId] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [precio, setPrecio] = useState(0);

  const [abierta, setAbierta] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    const [provs, prods, comps] = await Promise.all([
      api<Proveedor[]>("/proveedores"),
      api<Producto[]>("/productos"),
      api<Compra[]>("/compras"),
    ]);
    setProveedores(provs);
    setProductos(prods);
    setCompras(comps);
  }

  useEffect(() => {
    cargar();
  }, []);

  function agregarItem() {
    const p = productos.find((x) => x.id === productoId);
    if (!p || !cantidad) return;
    setItems((prev) => [
      ...prev,
      {
        producto_id: p.id,
        nombre: p.nombre,
        cantidad: Number(cantidad),
        precio_unitario: precio,
      },
    ]);
    setProductoId("");
    setCantidad("");
    setPrecio(0);
  }

  async function guardar() {
    setError("");
    setMensaje("");
    try {
      await api("/compras", {
        method: "POST",
        body: JSON.stringify({
          proveedor_id: proveedorId,
          items: items.map((i) => ({
            producto_id: i.producto_id,
            cantidad: i.cantidad,
            precio_unitario: i.precio_unitario,
          })),
        }),
      });
      setMensaje("Compra registrada. El stock fue incrementado.");
      setItems([]);
      setProveedorId("");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function anular(id: string) {
    if (!window.confirm("¿Anular esta compra? Se descontará el stock.")) return;
    await api(`/compras/${id}/anular`, { method: "POST" });
    await cargar();
  }

  const total = items.reduce((s, i) => s + i.cantidad * i.precio_unitario, 0);
  const nombreProveedor = (id: string) =>
    proveedores.find((p) => p.id === id)?.nombre ?? "—";

  return (
    <div>
      <h2>Compras</h2>

      <section className="card">
        <h3>Registrar compra</h3>
        <label>
          Proveedor
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

        <div className="inline-form" style={{ marginTop: 10 }}>
          <select
            value={productoId}
            onChange={(e) => setProductoId(e.target.value)}
          >
            <option value="">Producto...</option>
            {productos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Cantidad"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
          />
          <MoneyInput
            placeholder="Costo unitario"
            value={precio}
            onChange={setPrecio}
          />
          <button type="button" onClick={agregarItem}>
            Agregar
          </button>
        </div>

        {items.length > 0 && (
          <table style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cant.</th>
                <th>Costo</th>
                <th>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i, idx) => (
                <tr key={idx}>
                  <td>{i.nombre}</td>
                  <td>{i.cantidad}</td>
                  <td>{formatMoney(i.precio_unitario)}</td>
                  <td>{formatMoney(i.cantidad * i.precio_unitario)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="total">{formatMoney(total)}</div>

        <button
          className="primary"
          disabled={!proveedorId || items.length === 0}
          onClick={guardar}
        >
          Guardar compra
        </button>
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="card">
        <h3>Historial de compras</h3>
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Proveedor</th>
              <th>Total</th>
              <th>Estado</th>
              {user?.rol === "admin" && <th></th>}
            </tr>
          </thead>
          <tbody>
            {compras.map((c) => (
              <Fragment key={c.id}>
                <tr
                  className="venta-row"
                  onClick={() => setAbierta(abierta === c.id ? null : c.id)}
                >
                  <td>
                    {new Date(c.fecha).toLocaleString("es-ES", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td>{nombreProveedor(c.proveedor_id)}</td>
                  <td>{formatMoney(c.total)}</td>
                  <td>
                    <span className={c.anulada ? "pill off" : "pill on"}>
                      {c.anulada ? "Anulada" : "Registrada"}
                    </span>
                  </td>
                  {user?.rol === "admin" && (
                    <td onClick={(e) => e.stopPropagation()}>
                      {!c.anulada && (
                        <button className="ghost" onClick={() => anular(c.id)}>
                          Anular
                        </button>
                      )}
                    </td>
                  )}
                </tr>
                {abierta === c.id && (
                  <tr>
                    <td colSpan={user?.rol === "admin" ? 5 : 4}>
                      <div className="detail-panel">
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
                              {d.nombre_producto} × {d.cantidad}
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
