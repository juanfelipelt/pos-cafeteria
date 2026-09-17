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

interface Insumo {
  id: string;
  nombre: string;
  unidad: string;
}

interface ItemCompra {
  tipo: "producto" | "insumo";
  ref_id: string;
  nombre: string;
  unidad: string;
  cantidad: number;
  precio_unitario: number;
}

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
  const [insumos, setInsumos] = useState<Insumo[]>([]);
  const [compras, setCompras] = useState<Compra[]>([]);

  const [proveedorId, setProveedorId] = useState("");
  const [items, setItems] = useState<ItemCompra[]>([]);
  const [tipoLinea, setTipoLinea] = useState<"producto" | "insumo">("producto");
  const [refId, setRefId] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [precio, setPrecio] = useState(0);

  const [abierta, setAbierta] = useState<string | null>(null);
  const [editandoCompraId, setEditandoCompraId] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    const [provs, prods, ins, comps] = await Promise.all([
      api<Proveedor[]>("/proveedores"),
      api<Producto[]>("/productos"),
      api<Insumo[]>("/insumos?solo_activos=true"),
      api<Compra[]>("/compras"),
    ]);
    setProveedores(provs);
    setProductos(prods);
    setInsumos(ins);
    setCompras(comps);
  }

  useEffect(() => {
    cargar();
  }, []);

  function agregarItem() {
    if (!refId || !cantidad) return;
    if (tipoLinea === "producto") {
      const p = productos.find((x) => x.id === refId);
      if (!p) return;
      setItems((prev) => [
        ...prev,
        {
          tipo: "producto",
          ref_id: p.id,
          nombre: p.nombre,
          unidad: "",
          cantidad: Number(cantidad),
          precio_unitario: precio,
        },
      ]);
    } else {
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
    setRefId("");
    setCantidad("");
    setPrecio(0);
  }

  function actualizarItem(
    idx: number,
    campo: "cantidad" | "precio_unitario",
    valor: number
  ) {
    setItems((prev) =>
      prev.map((it, i) => (i === idx ? { ...it, [campo]: valor } : it))
    );
  }

  function quitarItem(idx: number) {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  }

  function editarCompra(c: Compra) {
    setEditandoCompraId(c.id);
    setProveedorId(c.proveedor_id);
    setItems(
      c.detalles.map((d) => {
        const tipo = d.tipo === "insumo" ? "insumo" : "producto";
        const ref_id =
          tipo === "insumo" ? d.insumo_id ?? "" : d.producto_id ?? "";
        const nombre =
          d.nombre || d.nombre_producto || d.nombre_insumo || "—";
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
    setMensaje("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelarEdicion() {
    setEditandoCompraId(null);
    setItems([]);
    setProveedorId("");
    setMensaje("");
  }

  async function guardar() {
    setError("");
    setMensaje("");
    const payload = {
      proveedor_id: proveedorId,
      items: items.map((i) => ({
        tipo: i.tipo,
        producto_id: i.tipo === "producto" ? i.ref_id : null,
        insumo_id: i.tipo === "insumo" ? i.ref_id : null,
        cantidad: i.cantidad,
        precio_unitario: i.precio_unitario,
      })),
    };
    try {
      if (editandoCompraId) {
        await api(`/compras/${editandoCompraId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setMensaje("Compra actualizada.");
      } else {
        await api("/compras", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setMensaje("Compra registrada.");
      }
      setItems([]);
      setProveedorId("");
      setEditandoCompraId(null);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function anular(id: string) {
    if (!window.confirm("¿Anular esta compra? Se revertirá el stock.")) return;
    setError("");
    try {
      await api(`/compras/${id}/anular`, { method: "POST" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function eliminar(id: string) {
    if (
      !window.confirm("¿Estás seguro de eliminar esta compra? Se revertirá el stock.")
    )
      return;
    setError("");
    try {
      await api(`/compras/${id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  const total = items.reduce((s, i) => s + i.cantidad * i.precio_unitario, 0);
  const nombreProveedor = (id: string) =>
    proveedores.find((p) => p.id === id)?.nombre ?? "—";
  const nombreDetalle = (d: DetalleCompra) =>
    d.nombre ?? d.nombre_producto ?? d.nombre_insumo ?? "—";

  return (
    <div>
      <h2>Compras</h2>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h3>{editandoCompraId ? "Editar compra" : "Registrar compra"}</h3>
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

        <div className="chips" style={{ marginTop: 12 }}>
          <button
            className={tipoLinea === "producto" ? "chip active" : "chip"}
            onClick={() => {
              setTipoLinea("producto");
              setRefId("");
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

        <div className="inline-form" style={{ marginTop: 10 }}>
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
                <th>Tipo</th>
                <th>Nombre</th>
                <th>Cant.</th>
                <th>Costo</th>
                <th>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((i, idx) => (
                <tr key={idx}>
                  <td data-label="Tipo">{i.tipo}</td>
                  <td data-label="Nombre" className="cell-main">
                    {i.nombre}
                    {i.unidad ? ` (${i.unidad})` : ""}
                  </td>
                  <td data-label="Cant.">
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
                    <MoneyInput
                      value={i.precio_unitario}
                      onChange={(v) => actualizarItem(idx, "precio_unitario", v)}
                    />
                  </td>
                  <td data-label="Subtotal">
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

        <div className="total">{formatMoney(total)}</div>

        <div className="inline-form" style={{ marginTop: 4 }}>
          <button
            className="primary"
            disabled={!proveedorId || items.length === 0}
            onClick={guardar}
          >
            {editandoCompraId ? "Guardar cambios" : "Guardar compra"}
          </button>
          {editandoCompraId && (
            <button className="ghost" onClick={cancelarEdicion}>
              Cancelar
            </button>
          )}
        </div>
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
                  <td data-label="Fecha">
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
                    <span className={c.anulada ? "pill off" : "pill on"}>
                      {c.anulada ? "Anulada" : "Registrada"}
                    </span>
                  </td>
                  {user?.rol === "admin" && (
                    <td
                      className="no-label"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="actions">
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
                {abierta === c.id && (
                  <tr className="detalle-row">
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
