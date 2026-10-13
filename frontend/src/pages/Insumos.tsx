/*
 * ARCHIVO: src/pages/Insumos.tsx
 * -----------------------------------------------------------------------------
 * ¿Qué es?
 *   Pantalla (página) "Insumos" de Cafetería POS, el sistema de gestión de la cafetería.
 *   Los "insumos" son las materias primas (ej. café molido, leche, azúcar) que
 *   se usan para preparar los productos que se venden.
 *
 * ¿Para qué sirve?
 *   - Mostrar la tabla con todos los insumos: nombre, unidad, stock, costo,
 *     proveedor y estado (activo/inactivo).
 *   - Permitir al administrador crear un insumo nuevo con un formulario.
 *   - Permitir al administrador editar un insumo en una ventana modal,
 *     activarlo/desactivarlo y eliminarlo.
 *   Los usuarios que no son admin sólo pueden ver la lista.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se monta como ruta "/insumos" dentro de <App /> (App.tsx), protegida por
 *     login y envuelta por <Layout />.
 *   - Usa {api} (src/api.ts) para hablar con el backend.
 *   - Usa {useAuth} (src/auth.tsx) para saber el rol (admin o no).
 *   - Los insumos creados aquí se usan luego en Compras (para comprarlos) y en
 *     Costeo (para calcular cuánto cuesta preparar cada producto).
 *   - Usa <MoneyInput /> para el costo y {formatMoney} para mostrarlo.
 * -----------------------------------------------------------------------------
 */

// --- Importaciones -----------------------------------------------------------
import { useEffect, useState } from "react"; // Hooks de React para estado y efectos.
import { api } from "../api"; // Cliente HTTP con el token incluido.
import MoneyInput from "../components/MoneyInput"; // Campo especial para valores de dinero.
import { useAuth } from "../auth"; // Hook para conocer el usuario y su rol.
import { formatMoney } from "../lib/format"; // Convierte números a texto con formato de moneda.

// --- Tipos de datos ----------------------------------------------------------

// Un insumo (materia prima) tal como lo devuelve el backend.
interface Insumo {
  id: string;
  nombre: string;
  unidad: string;
  stock: number; // Cantidad disponible en inventario.
  costo_unitario: number; // Costo por una unidad de medida.
  proveedor_id: string | null; // Proveedor asociado; null = "sin proveedor".
  estado: boolean; // true = activo, false = inactivo.
}

// Proveedor: sólo id y nombre, para el desplegable de "proveedor del insumo".
interface Proveedor {
  id: string;
  nombre: string;
}

// Lista fija de unidades de medida que se pueden elegir (gramos, kilos, etc.).
const UNIDADES = ["g", "kg", "ml", "L", "unidad", "paquete", "paca", "caja"];

// Componente principal de la página.
export default function Insumos() {
  const { user } = useAuth(); // Usuario logueado.
  const esAdmin = user?.rol === "admin"; // Bandera: ¿el usuario es administrador? Controla qué puede hacer.

  // --- Estados con las listas traídas del backend ---
  const [insumos, setInsumos] = useState<Insumo[]>([]); // Todos los insumos.
  const [proveedores, setProveedores] = useState<Proveedor[]>([]); // Proveedores disponibles.

  // --- Estados del formulario "Nuevo insumo" ---
  const [nombre, setNombre] = useState(""); // Nombre escrito.
  const [unidad, setUnidad] = useState("g"); // Unidad elegida (por defecto gramos).
  const [stock, setStock] = useState(""); // Stock inicial (como texto).
  const [costo, setCosto] = useState(0); // Costo unitario (número, viene de MoneyInput).
  const [proveedorId, setProveedorId] = useState(""); // Proveedor elegido.

  // --- Estados de la interfaz ---
  const [editando, setEditando] = useState<Insumo | null>(null); // Insumo que se está editando en el modal (null = modal cerrado).
  const [error, setError] = useState(""); // Mensaje de error.
  const [ok, setOk] = useState(""); // Mensaje de éxito.

  // Carga en paralelo los insumos y los proveedores desde el backend.
  async function cargar() {
    const [ins, provs] = await Promise.all([
      api<Insumo[]>("/insumos"),
      api<Proveedor[]>("/proveedores"),
    ]);
    setInsumos(ins);
    setProveedores(provs);
  }

  // Al montar la página, cargamos los datos una sola vez.
  useEffect(() => {
    cargar();
  }, []);

  // Maneja el envío del formulario de creación de insumo.
  async function crear(e: React.FormEvent) {
    e.preventDefault(); // Evita que el navegador recargue la página al enviar el formulario.
    setError("");
    setOk("");
    try {
      // POST al backend con los datos del nuevo insumo.
      await api("/insumos", {
        method: "POST",
        body: JSON.stringify({
          nombre,
          unidad,
          stock: Number(stock) || 0, // Si el stock está vacío o no es número, se envía 0.
          costo_unitario: costo,
          proveedor_id: proveedorId || null, // Cadena vacía => null (sin proveedor).
        }),
      });
      // Limpiamos el formulario para dejarlo listo para el siguiente insumo.
      setNombre("");
      setUnidad("g");
      setStock("");
      setCosto(0);
      setProveedorId("");
      setOk("Insumo creado.");
      await cargar(); // Refrescamos la tabla.
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Guarda los cambios del insumo que se está editando en el modal.
  async function guardarEdicion() {
    if (!editando) return; // Si no hay nada que editar, no hacemos nada.
    setError("");
    try {
      // PUT al backend con el id del insumo y sus nuevos valores.
      await api(`/insumos/${editando.id}`, {
        method: "PUT",
        body: JSON.stringify({
          nombre: editando.nombre,
          unidad: editando.unidad,
          stock: editando.stock,
          costo_unitario: editando.costo_unitario,
          proveedor_id: editando.proveedor_id,
        }),
      });
      setEditando(null); // Cerramos el modal.
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Activa o desactiva un insumo (envía lo contrario de su estado actual).
  async function cambiarEstado(i: Insumo) {
    await api(`/insumos/${i.id}/estado`, {
      method: "PATCH", // PATCH porque sólo cambiamos un campo concreto.
      body: JSON.stringify({ estado: !i.estado }),
    });
    await cargar();
  }

  // Elimina un insumo, pidiendo confirmación primero.
  async function eliminar(i: Insumo) {
    if (!window.confirm(`¿Eliminar el insumo "${i.nombre}"?`)) return;
    setError("");
    try {
      await api(`/insumos/${i.id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Dado el id de un proveedor, devuelve su nombre (o "—" si no tiene o no existe).
  const proveedorDe = (id: string | null) =>
    proveedores.find((p) => p.id === id)?.nombre ?? "—";

  // --- Render de la pantalla (JSX) -------------------------------------------
  return (
    <div>
      <h2>Insumos</h2>

      {/* Formulario de creación: sólo visible para administradores */}
      {esAdmin && (
        <form onSubmit={crear} className="card">
          <h3>Nuevo insumo</h3>
          <div className="inline-form">
            {/* Campo de nombre (obligatorio) */}
            <input
              placeholder="Nombre (ej. Café molido)"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />
            {/* Desplegable de unidades de medida */}
            <select value={unidad} onChange={(e) => setUnidad(e.target.value)}>
              {UNIDADES.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
            {/* Stock inicial (número decimal) */}
            <input
              placeholder="Stock"
              type="number"
              step="any"
              value={stock}
              onChange={(e) => setStock(e.target.value)}
            />
            {/* Costo unitario con formato de moneda */}
            <MoneyInput placeholder="Costo unitario" value={costo} onChange={setCosto} />
            {/* Proveedor (con opción "Sin proveedor") */}
            <select
              value={proveedorId}
              onChange={(e) => setProveedorId(e.target.value)}
            >
              <option value="">Sin proveedor</option>
              {proveedores.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" className="primary">
              Guardar
            </button>
          </div>
          {ok && <p className="ok">{ok}</p>}
          {error && <p className="error">{error}</p>}
        </form>
      )}

      {/* Si NO es admin, igual mostramos los errores (no puede crear pero sí ver) */}
      {!esAdmin && error && <p className="error">{error}</p>}

      {/* Tarjeta con la tabla de insumos */}
      <section className="card">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Unidad</th>
              <th>Stock</th>
              <th>Costo unitario</th>
              <th>Proveedor</th>
              <th>Estado</th>
              {/* Columna de acciones sólo para admin */}
              {esAdmin && <th></th>}
            </tr>
          </thead>
          <tbody>
            {/* Una fila por cada insumo */}
            {insumos.map((i) => (
              <tr key={i.id}>
                <td data-label="Nombre" className="cell-main">
                  {i.nombre}
                </td>
                <td data-label="Unidad">{i.unidad}</td>
                <td data-label="Stock">{i.stock}</td>
                <td data-label="Costo unitario">{formatMoney(i.costo_unitario)}</td>
                <td data-label="Proveedor">{proveedorDe(i.proveedor_id)}</td>
                <td data-label="Estado">
                  {/* Píldora que cambia de color según el estado del insumo */}
                  <span className={i.estado ? "pill on" : "pill off"}>
                    {i.estado ? "Activo" : "Inactivo"}
                  </span>
                </td>
                {/* Celda de acciones sólo para admin */}
                {esAdmin && (
                  <td className="no-label">
                    <div className="actions">
                      {/* Abre el modal de edición con este insumo */}
                      <button className="ghost" onClick={() => setEditando(i)}>
                        Editar
                      </button>
                      {/* El texto del botón cambia según el estado actual */}
                      <button className="ghost" onClick={() => cambiarEstado(i)}>
                        {i.estado ? "Desactivar" : "Activar"}
                      </button>
                      <button
                        className="ghost danger"
                        onClick={() => eliminar(i)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {/* Si no hay insumos, mostramos un mensaje ocupando todas las columnas */}
            {insumos.length === 0 && (
              <tr>
                <td colSpan={esAdmin ? 7 : 6} className="muted">
                  Aún no hay insumos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {/* Modal de edición: sólo se dibuja si "editando" tiene un insumo */}
      {editando && (
        // Al hacer clic en el fondo oscuro se cierra el modal
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          {/* stopPropagation evita que un clic dentro del modal lo cierre */}
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar insumo</h3>
            <div
              className="inline-form"
              style={{ flexDirection: "column", alignItems: "stretch" }}
            >
              {/* Cada input actualiza una copia del insumo en edición con setEditando({...editando, campo}) */}
              <input
                placeholder="Nombre"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
              <select
                value={editando.unidad}
                onChange={(e) =>
                  setEditando({ ...editando, unidad: e.target.value })
                }
              >
                {UNIDADES.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
              <input
                placeholder="Stock"
                type="number"
                step="any"
                value={editando.stock}
                onChange={(e) =>
                  setEditando({ ...editando, stock: Number(e.target.value) })
                }
              />
              <MoneyInput
                placeholder="Costo unitario"
                value={editando.costo_unitario}
                onChange={(v) =>
                  setEditando({ ...editando, costo_unitario: v })
                }
              />
              <select
                value={editando.proveedor_id ?? ""}
                onChange={(e) =>
                  setEditando({
                    ...editando,
                    proveedor_id: e.target.value || null, // "" => null
                  })
                }
              >
                <option value="">Sin proveedor</option>
                {proveedores.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              {/* Cerrar sin guardar */}
              <button className="ghost" onClick={() => setEditando(null)}>
                Cancelar
              </button>
              {/* Guardar los cambios en el backend */}
              <button className="primary" onClick={guardarEdicion}>
                Guardar
              </button>
            </div>
            {error && <p className="error">{error}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
