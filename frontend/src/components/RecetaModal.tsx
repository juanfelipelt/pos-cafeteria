/*
 * ============================================================================
 * RecetaModal.tsx  ·  Ventana modal para editar la "receta" de un producto
 * ============================================================================
 * ¿Qué es?
 *   Una ventana emergente (modal) que permite definir de qué está hecho un
 *   producto: sus "componentes". Sirve tanto para productos elaborados
 *   (que usan INSUMOS) como para combos (productos "compuestos" que además
 *   pueden incluir otros PRODUCTOS como componentes).
 *
 * ¿Para qué sirve?
 *   - Listar los componentes actuales de la receta del producto.
 *   - Agregar componentes (insumo o producto) con una cantidad.
 *   - Quitar componentes.
 *   - Calcular y mostrar el costo total de los insumos usados.
 *   - Guardar la receta en el backend.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se importa y abre desde la página `Productos.tsx` al pulsar "Receta".
 *   - Usa `api` (de `../api`) para leer/guardar en el backend.
 *   - Usa `formatMoney` (de `../lib/format`) para mostrar dinero con formato.
 *   - Recibe por props los datos del producto y dos funciones de retorno
 *     (callbacks): `onClose` (cerrar) y `onSaved` (avisar que se guardó).
 * ============================================================================
 */

// Hooks de React: useEffect para efectos y useState para el estado local.
import { useEffect, useState } from "react";
// Helper para llamar al backend (GET, PUT, etc.).
import { api } from "../api";
// Helper que da formato de moneda a números (ej: 1.234,50).
import { formatMoney } from "../lib/format";

// Tipo que representa un insumo (materia prima) que se puede usar en una receta.
interface Insumo {
  id: string;
  nombre: string;
  unidad: string; // Unidad de medida (gramos, litros, unidades...).
  costo_unitario: number; // Precio por unidad, para calcular el costo.
}

// Versión reducida de un producto, para usarla como componente de un combo.
interface ProductoLite {
  id: string;
  nombre: string;
  tipo: string;
}

// Tipo que representa una fila de la receta (un componente con su cantidad).
interface Fila {
  tipo: "insumo" | "producto"; // De qué clase de componente se trata.
  componente_id: string; // Id del insumo o del producto.
  cantidad: number; // Cuánto se usa de ese componente.
}

// Props (datos de entrada) que recibe el modal desde su componente padre.
interface Props {
  productoId: string; // Id del producto cuya receta editamos.
  productoNombre: string; // Nombre del producto (para el título).
  productoTipo: string; // Tipo del producto; si es "compuesto" es un combo.
  onClose: () => void; // Callback para cerrar el modal sin guardar.
  onSaved: () => void; // Callback tras guardar correctamente.
}

export default function RecetaModal({
  productoId,
  productoNombre,
  productoTipo,
  onClose,
  onSaved,
}: Props) {
  // Un producto es "combo/compuesto" cuando su tipo es "compuesto".
  // Solo en ese caso se permite añadir otros productos como componentes.
  const esCombo = productoTipo === "compuesto";

  // --- Estados locales del modal ---
  // Lista de insumos disponibles (traída del backend).
  const [insumos, setInsumos] = useState<Insumo[]>([]);
  // Lista de productos disponibles para usar como componente (solo combos).
  const [productos, setProductos] = useState<ProductoLite[]>([]);
  // Filas que forman la receta actual (los componentes ya agregados).
  const [filas, setFilas] = useState<Fila[]>([]);
  // Tipo del componente que se va a agregar en este momento.
  const [tipo, setTipo] = useState<"insumo" | "producto">("insumo");
  // Id del componente seleccionado en el desplegable (vacío = ninguno).
  const [componenteId, setComponenteId] = useState("");
  // Cantidad escrita para el componente a agregar (se guarda como texto).
  const [cantidad, setCantidad] = useState("");
  // Mensaje de error a mostrar (vacío = sin error).
  const [error, setError] = useState("");

  // Carga desde el backend los insumos y la receta ya existente del producto.
  async function cargar() {
    // Preparamos las peticiones que se lanzarán en paralelo.
    const requests: Promise<unknown>[] = [
      // Solo traemos insumos activos (los inactivos no se usan en recetas).
      api<Insumo[]>("/insumos?solo_activos=true"),
      // Receta actual del producto.
      api<{ tipo: string; componente_id: string; cantidad: number }[]>(
        `/productos/${productoId}/receta`
      ),
    ];
    // Solo para combos, además pedimos la lista de productos disponibles.
    if (esCombo) requests.push(api<ProductoLite[]>("/productos"));
    // Esperamos a que TODAS las peticiones terminen (en paralelo = más rápido).
    const [ins, receta, prods] = await Promise.all(requests);
    // Guardamos los insumos en el estado.
    setInsumos(ins as Insumo[]);
    // Guardamos los productos (o un arreglo vacío si no aplica).
    setProductos((prods as ProductoLite[]) ?? []);
    // Convertimos la receta recibida en filas del estado.
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

  // Al montar el modal, cargamos los datos. Si algo falla, mostramos error.
  useEffect(() => {
    cargar().catch((err) =>
      setError(err instanceof Error ? err.message : "Error")
    );
    // El arreglo vacío [] significa que este efecto corre UNA sola vez.
    // (Se desactiva la regla de lint porque cargar depende de props estables.)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Agrega la fila seleccionada (componente + cantidad) a la receta.
  function agregar() {
    // Si no se eligió componente o no hay cantidad, no hacemos nada.
    if (!componenteId || !cantidad) return;
    // Evitamos duplicados: un mismo componente no puede repetirse en la receta.
    if (filas.some((f) => f.tipo === tipo && f.componente_id === componenteId)) {
      setError("Ese componente ya está en la receta.");
      return;
    }
    // Agregamos la nueva fila al final (sin mutar el arreglo anterior).
    // Convertimos la cantidad de texto a número con Number().
    setFilas((prev) => [
      ...prev,
      { tipo, componente_id: componenteId, cantidad: Number(cantidad) },
    ]);
    // Limpiamos los campos del formulario para la siguiente captura.
    setComponenteId("");
    setCantidad("");
    setError("");
  }

  // Quita una fila de la receta. Recibe la fila a eliminar.
  function quitar(f: Fila) {
    setFilas((prev) =>
      // Conservamos solo las filas distintas a la indicada (mismo tipo e id).
      prev.filter(
        (x) => !(x.tipo === f.tipo && x.componente_id === f.componente_id)
      )
    );
  }

  // Guarda la receta en el backend pulsando el botón "Guardar receta".
  async function guardar() {
    setError(""); // Limpiamos errores previos.
    try {
      // Enviamos la receta completa con PUT (reemplaza los componentes).
      await api(`/productos/${productoId}/receta`, {
        method: "PUT",
        body: JSON.stringify({
          // Transformamos las filas al formato que espera el backend:
          // un insumo usa `insumo_id`, un producto usa `componente_producto_id`.
          items: filas.map((f) => ({
            tipo: f.tipo,
            insumo_id: f.tipo === "insumo" ? f.componente_id : null,
            componente_producto_id: f.tipo === "producto" ? f.componente_id : null,
            cantidad: f.cantidad,
          })),
        }),
      });
      // Si salió bien, avisamos al padre y cerramos el modal.
      onSaved();
      onClose();
    } catch (err) {
      // Si falló, mostramos el mensaje de error.
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Busca un insumo por su id dentro de la lista cargada.
  const insumoDe = (id: string) => insumos.find((i) => i.id === id);
  // Busca un producto por su id dentro de la lista cargada.
  const productoDe = (id: string) => productos.find((p) => p.id === id);

  // Calcula el costo de una fila. Para insumos: costo unitario × cantidad.
  const costoFila = (f: Fila): number => {
    if (f.tipo === "insumo") {
      return (insumoDe(f.componente_id)?.costo_unitario ?? 0) * f.cantidad;
    }
    return 0; // el costo del producto componente se ve al guardar (puede ser recursivo)
  };
  // Suma el costo de todas las filas para obtener el costo total de la receta.
  const costoTotal = filas.reduce((s, f) => s + costoFila(f), 0);

  // Devuelve el nombre legible de una fila (insumo con su unidad, o producto).
  const nombreFila = (f: Fila): string => {
    if (f.tipo === "insumo") {
      const i = insumoDe(f.componente_id);
      // Si encontramos el insumo, mostramos "nombre (unidad)"; si no, el id.
      return i ? `${i.nombre}${i.unidad ? ` (${i.unidad})` : ""}` : f.componente_id;
    }
    // Para productos mostramos su nombre; si no lo encontramos, el id.
    return productoDe(f.componente_id)?.nombre ?? f.componente_id;
  };

  // --- Marcado (JSX) del modal ---
  return (
    // Fondo oscuro del modal: si hacen clic fuera de la caja, se cierra.
    <div className="modal-overlay" onClick={onClose}>
      {/* Caja blanca del modal. stopPropagation evita que el clic de adentro
          se propague al overlay y cierre el modal sin querer. */}
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {/* Título: nombre del producto y aviso "(combo)" si es compuesto. */}
        <h3>
          Receta · {productoNombre} {esCombo && "(combo)"}
        </h3>

        {/* Selector Insumo/Producto: solo aparece para productos compuestos. */}
        {esCombo && (
          <div className="chips" style={{ marginBottom: 8 }}>
            {/* Botón para elegir componente tipo "insumo". */}
            <button
              type="button"
              className={tipo === "insumo" ? "chip active" : "chip"}
              onClick={() => {
                setTipo("insumo");
                setComponenteId(""); // Reseteamos la selección al cambiar de tipo.
              }}
            >
              Insumo
            </button>
            {/* Botón para elegir componente tipo "producto". */}
            <button
              type="button"
              className={tipo === "producto" ? "chip active" : "chip"}
              onClick={() => {
                setTipo("producto");
                setComponenteId(""); // Reseteamos la selección al cambiar de tipo.
              }}
            >
              Producto
            </button>
          </div>
        )}

        {/* Formulario en línea para agregar un componente a la receta. */}
        <div className="inline-form">
          {/* Desplegable que lista insumos o productos según el tipo elegido. */}
          <select
            value={componenteId}
            onChange={(e) => setComponenteId(e.target.value)}
          >
            {/* Opción vacía (placeholder) según el tipo actual. */}
            <option value="">
              {tipo === "insumo" ? "Insumo..." : "Producto..."}
            </option>
            {/* Si el tipo es insumo, listamos insumos con su unidad;
                si es producto, listamos productos excluyendo el propio. */}
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
          {/* Campo numérico para la cantidad. step="any" permite decimales. */}
          <input
            type="number"
            step="any"
            placeholder="Cantidad"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
          />
          {/* Botón que agrega la fila a la receta. */}
          <button type="button" onClick={agregar}>
            Agregar
          </button>
        </div>

        {/* Tabla con los componentes ya agregados a la receta. */}
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
            {/* Recorremos las filas; la key combina tipo e id para ser única. */}
            {filas.map((f) => (
              <tr key={`${f.tipo}-${f.componente_id}`}>
                <td data-label="Componente" className="cell-main">
                  {nombreFila(f)}
                </td>
                <td data-label="Tipo">{f.tipo}</td>
                <td data-label="Cantidad">{f.cantidad}</td>
                {/* El costo solo se muestra para insumos; para productos es "—". */}
                <td data-label="Costo">
                  {f.tipo === "insumo" ? formatMoney(costoFila(f)) : "—"}
                </td>
                <td className="no-label">
                  {/* Botón para quitar esta fila de la receta. */}
                  <button className="ghost danger" onClick={() => quitar(f)}>
                    Quitar
                  </button>
                </td>
              </tr>
            ))}
            {/* Si no hay componentes, mostramos una fila informativa. */}
            {filas.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  Sin componentes en la receta.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Resumen del costo total de los insumos de la receta. */}
        <p style={{ marginTop: 12, fontWeight: 600 }}>
          Costo total: {formatMoney(costoTotal)}
          {/* Aviso para combos: no se incluye el costo de los productos. */}
          {esCombo && " (sin productos componentes)"}
        </p>

        {/* Solo mostramos el error si `error` tiene contenido. */}
        {error && <p className="error">{error}</p>}

        {/* Botones de acción: cancelar (cierra sin guardar) y guardar. */}
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
