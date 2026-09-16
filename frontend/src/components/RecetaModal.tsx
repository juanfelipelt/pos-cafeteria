import { useEffect, useState } from "react";
import { api } from "../api";
import { formatMoney } from "../lib/format";

interface Insumo {
  id: string;
  nombre: string;
  unidad: string;
  costo_unitario: number;
}

interface ProductoLite {
  id: string;
  nombre: string;
  tipo: string;
}

interface Fila {
  tipo: "insumo" | "producto";
  componente_id: string;
  cantidad: number;
}

interface Props {
  productoId: string;
  productoNombre: string;
  productoTipo: string;
  onClose: () => void;
  onSaved: () => void;
}

export default function RecetaModal({
  productoId,
  productoNombre,
  productoTipo,
  onClose,
  onSaved,
}: Props) {
  const esCombo = productoTipo === "compuesto";

  const [insumos, setInsumos] = useState<Insumo[]>([]);
  const [productos, setProductos] = useState<ProductoLite[]>([]);
  const [filas, setFilas] = useState<Fila[]>([]);
  const [tipo, setTipo] = useState<"insumo" | "producto">("insumo");
  const [componenteId, setComponenteId] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    const requests: Promise<unknown>[] = [
      api<Insumo[]>("/insumos?solo_activos=true"),
      api<{ tipo: string; componente_id: string; cantidad: number }[]>(
        `/productos/${productoId}/receta`
      ),
    ];
    if (esCombo) requests.push(api<ProductoLite[]>("/productos"));
    const [ins, receta, prods] = await Promise.all(requests);
    setInsumos(ins as Insumo[]);
    setProductos((prods as ProductoLite[]) ?? []);
    setFilas(
      (receta as { tipo: "insumo" | "producto"; componente_id: string; cantidad: number }[]).map(
        (r) => ({
          tipo: r.tipo,
          componente_id: r.componente_id,
          cantidad: r.cantidad,
        })
      )
    );
  }

  useEffect(() => {
    cargar().catch((err) =>
      setError(err instanceof Error ? err.message : "Error")
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function agregar() {
    if (!componenteId || !cantidad) return;
    if (filas.some((f) => f.tipo === tipo && f.componente_id === componenteId)) {
      setError("Ese componente ya está en la receta.");
      return;
    }
    setFilas((prev) => [
      ...prev,
      { tipo, componente_id: componenteId, cantidad: Number(cantidad) },
    ]);
    setComponenteId("");
    setCantidad("");
    setError("");
  }

  function quitar(f: Fila) {
    setFilas((prev) =>
      prev.filter(
        (x) => !(x.tipo === f.tipo && x.componente_id === f.componente_id)
      )
    );
  }

  async function guardar() {
    setError("");
    try {
      await api(`/productos/${productoId}/receta`, {
        method: "PUT",
        body: JSON.stringify({
          items: filas.map((f) => ({
            tipo: f.tipo,
            insumo_id: f.tipo === "insumo" ? f.componente_id : null,
            componente_producto_id: f.tipo === "producto" ? f.componente_id : null,
            cantidad: f.cantidad,
          })),
        }),
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  const insumoDe = (id: string) => insumos.find((i) => i.id === id);
  const productoDe = (id: string) => productos.find((p) => p.id === id);

  const costoFila = (f: Fila): number => {
    if (f.tipo === "insumo") {
      return (insumoDe(f.componente_id)?.costo_unitario ?? 0) * f.cantidad;
    }
    return 0; // el costo del producto componente se ve al guardar (puede ser recursivo)
  };
  const costoTotal = filas.reduce((s, f) => s + costoFila(f), 0);

  const nombreFila = (f: Fila): string => {
    if (f.tipo === "insumo") {
      const i = insumoDe(f.componente_id);
      return i ? `${i.nombre}${i.unidad ? ` (${i.unidad})` : ""}` : f.componente_id;
    }
    return productoDe(f.componente_id)?.nombre ?? f.componente_id;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>
          Receta · {productoNombre} {esCombo && "(combo)"}
        </h3>

        {esCombo && (
          <div className="chips" style={{ marginBottom: 8 }}>
            <button
              type="button"
              className={tipo === "insumo" ? "chip active" : "chip"}
              onClick={() => {
                setTipo("insumo");
                setComponenteId("");
              }}
            >
              Insumo
            </button>
            <button
              type="button"
              className={tipo === "producto" ? "chip active" : "chip"}
              onClick={() => {
                setTipo("producto");
                setComponenteId("");
              }}
            >
              Producto
            </button>
          </div>
        )}

        <div className="inline-form">
          <select
            value={componenteId}
            onChange={(e) => setComponenteId(e.target.value)}
          >
            <option value="">
              {tipo === "insumo" ? "Insumo..." : "Producto..."}
            </option>
            {tipo === "insumo"
              ? insumos.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nombre} ({i.unidad})
                  </option>
                ))
              : productos
                  .filter((p) => p.id !== productoId)
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre}
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
          <button type="button" onClick={agregar}>
            Agregar
          </button>
        </div>

        <table style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Componente</th>
              <th>Tipo</th>
              <th>Cantidad</th>
              <th>Costo</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={`${f.tipo}-${f.componente_id}`}>
                <td data-label="Componente" className="cell-main">
                  {nombreFila(f)}
                </td>
                <td data-label="Tipo">{f.tipo}</td>
                <td data-label="Cantidad">{f.cantidad}</td>
                <td data-label="Costo">
                  {f.tipo === "insumo" ? formatMoney(costoFila(f)) : "—"}
                </td>
                <td className="no-label">
                  <button className="ghost danger" onClick={() => quitar(f)}>
                    Quitar
                  </button>
                </td>
              </tr>
            ))}
            {filas.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  Sin componentes en la receta.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <p style={{ marginTop: 12, fontWeight: 600 }}>
          Costo total: {formatMoney(costoTotal)}
          {esCombo && " (sin productos componentes)"}
        </p>

        {error && <p className="error">{error}</p>}

        <div className="modal-actions" style={{ marginTop: 16 }}>
          <button className="ghost" onClick={onClose}>
            Cancelar
          </button>
          <button className="primary" onClick={guardar}>
            Guardar receta
          </button>
        </div>
      </div>
    </div>
  );
}
