/*
 * Productos.tsx — Pantalla de administración de Productos y Categorías.
 *
 * ¿Qué es?
 *   Es la pantalla donde se administra el catálogo: qué productos vende el
 *   negocio y en qué categorías se agrupan.
 *
 * ¿Para qué sirve?
 *   - Crear categorías y renombrarlas.
 *   - Crear productos (nombre, precio, stock, categoría, tipo e imagen).
 *   - Editar un producto existente en un modal.
 *   - Activar / desactivar productos (sin borrarlos).
 *   - Abrir el modal de "Receta" para productos preparados o compuestos.
 *   - Filtrar la tabla por categoría.
 *   - Subir una imagen de producto (se comprime antes de guardarla).
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se monta en la ruta "/productos" (ver App.tsx), protegida por login.
 *   - Los productos activos y sus categorías son los que consume POS.tsx
 *     para armar las ventas.
 *   - Usa `useAuth` para mostrar el formulario de administración y las
 *     acciones (editar, activar, receta) solo a administradores.
 *   - Reutiliza MoneyInput, RecetaModal y las utilidades formatMoney e
 *     comprimirImagen, y habla con el backend mediante `api`.
 */

import { useEffect, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import RecetaModal from "../components/RecetaModal";
import { useAuth } from "../auth";
import { formatMoney } from "../lib/format";
import { comprimirImagen } from "../lib/image";

// Categoría tal como la devuelve el backend.
interface Categoria {
  id: string;
  nombre: string;
  descripcion: string;
  estado: boolean;
}

// Producto completo tal como lo devuelve el backend.
interface Producto {
  id: string;
  nombre: string;
  descripcion: string;
  categoria_id: string | null; // null = sin categoría
  imagen: string;
  precio: number;
  stock: number;
  estado: boolean; // activo / inactivo
  tipo: string; // "comprado" | "preparado" | "compuesto"
  costo: number;
}

// Datos que se editan en el modal de edición. Incluye solo lo modificable.
interface Editando {
  id: string;
  nombre: string;
  precio: number;
  stock: number;
  categoria_id: string;
  imagen: string;
  tipo: string;
}

// Componente principal de la pantalla de Productos.
export default function Productos() {
  // `user` = usuario logueado; define si es administrador.
  const { user } = useAuth();
  const [productos, setProductos] = useState<Producto[]>([]); // catálogo
  const [categorias, setCategorias] = useState<Categoria[]>([]); // categorías

  // --- Campos del formulario "Nuevo producto" ---
  const [nombre, setNombre] = useState("");
  const [precio, setPrecio] = useState(0);
  const [stock, setStock] = useState(""); // se guarda como texto y se convierte al enviar
  const [categoriaId, setCategoriaId] = useState("");
  const [imagen, setImagen] = useState(""); // imagen en base64 (comprimida)
  const [tipo, setTipo] = useState("comprado");

  // --- Estado de las categorías ---
  const [nuevaCategoria, setNuevaCategoria] = useState(""); // input para crear
  // Si no es null, esa categoría se está renombrando en línea.
  const [catEditando, setCatEditando] = useState<{ id: string; nombre: string } | null>(null);

  // --- Estado de modales y mensajes ---
  const [editando, setEditando] = useState<Editando | null>(null); // producto en edición
  const [recetaDe, setRecetaDe] = useState<Producto | null>(null); // producto para ver receta
  const [error, setError] = useState(""); // mensaje de error
  const [ok, setOk] = useState(""); // mensaje de éxito
  const [filtroCat, setFiltroCat] = useState<string | null>(null); // filtro por categoría

  // Atajo booleano: ¿el usuario actual es administrador?
  const esAdmin = user?.rol === "admin";

  // Carga en paralelo los productos y las categorías del backend.
  async function cargar() {
    const [ps, cs] = await Promise.all([
      api<Producto[]>("/productos"),
      api<Categoria[]>("/categorias"),
    ]);
    setProductos(ps);
    setCategorias(cs);
  }

  // Carga inicial: se ejecuta una sola vez al montar (arreglo []).
  useEffect(() => {
    cargar();
  }, []);

  // Maneja la imagen del formulario de creación:
  // toma el archivo elegido, lo comprime y guarda el resultado en base64.
  async function onImagen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setImagen(await comprimirImagen(file, { maxSize: 600, quality: 0.72 }));
    } catch {
      setError("No se pudo procesar la imagen.");
    }
  }

  // Igual que la anterior, pero para la imagen del modal de edición.
  async function onImagenEdit(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !editando) return;
    try {
      const imagen = await comprimirImagen(file, { maxSize: 600, quality: 0.72 });
      setEditando({ ...editando, imagen }); // actualiza solo la imagen del producto en edición
    } catch {
      setError("No se pudo procesar la imagen.");
    }
  }

  // Crea una categoría nueva a partir del formulario.
  async function crearCategoria(e: React.FormEvent) {
    e.preventDefault(); // evitamos que el formulario recargue la página
    setError("");
    try {
      await api("/categorias", {
        method: "POST",
        body: JSON.stringify({ nombre: nuevaCategoria }),
      });
      setNuevaCategoria(""); // limpiamos el input
      await cargar(); // recargamos para ver la nueva categoría
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Guarda el nuevo nombre de una categoría que se estaba editando.
  async function guardarCategoria() {
    if (!catEditando) return;
    await api(`/categorias/${catEditando.id}`, {
      method: "PUT",
      body: JSON.stringify({ nombre: catEditando.nombre }),
    });
    setCatEditando(null); // salimos del modo edición
    await cargar();
  }

  // Crea un producto nuevo con los datos del formulario.
  async function crearProducto(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setOk("");
    try {
      await api("/productos", {
        method: "POST",
        body: JSON.stringify({
          nombre,
          precio,
          // Number(stock) || 0: si el texto no es número válido, usamos 0.
          stock: Number(stock) || 0,
          categoria_id: categoriaId || null, // "" significa sin categoría
          imagen,
          tipo,
        }),
      });
      // Limpiamos el formulario tras crear el producto.
      setNombre("");
      setPrecio(0);
      setStock("");
      setCategoriaId("");
      setImagen("");
      setTipo("comprado");
      setOk("Producto creado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Guarda los cambios del producto que se edita en el modal.
  async function guardarEdicion() {
    if (!editando) return;
    setError("");
    setOk("");
    try {
      await api(`/productos/${editando.id}`, {
        method: "PUT",
        body: JSON.stringify({
          nombre: editando.nombre,
          precio: editando.precio,
          stock: editando.stock,
          categoria_id: editando.categoria_id || null,
          imagen: editando.imagen,
          tipo: editando.tipo,
        }),
      });
      setEditando(null); // cerramos el modal
      setOk("Producto actualizado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Cambia el estado (activo/inactivo) de un producto.
  // Envía el valor contrario al actual: !p.estado.
  async function cambiarEstado(p: Producto) {
    await api(`/productos/${p.id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: !p.estado }),
    });
    await cargar();
  }

  // Dado un id de categoría, devuelve su nombre. Si no existe, "—".
  const categoriaDe = (id: string | null) =>
    categorias.find((c) => c.id === id)?.nombre ?? "—";

  // Lista de productos que se muestran: filtrados por categoría o todos.
  const visibles = filtroCat
    ? productos.filter((p) => p.categoria_id === filtroCat)
    : productos;

  // Marcado que se dibuja en pantalla.
  return (
    <div>
      <h2>Productos</h2>

      {/* El bloque de administración (categorías y alta de productos)
          solo se muestra a los administradores. */}
      {esAdmin && (
        <>
          {/* Tarjeta para gestionar categorías. */}
          <section className="card">
            <h3>Categorías</h3>
            {/* Formulario para crear una categoría nueva. */}
            <form onSubmit={crearCategoria} className="inline-form">
              <input
                placeholder="Nueva categoría"
                value={nuevaCategoria}
                onChange={(e) => setNuevaCategoria(e.target.value)}
                required
              />
              <button type="submit" className="primary">
                Agregar
              </button>
            </form>
            <div className="chips" style={{ marginTop: 12 }}>
              {/* Por cada categoría: si es la que se está editando mostramos
                  un input con ✓ para guardar; si no, la mostramos como chip
                  con un lápiz ✎ para iniciar la edición. */}
              {categorias.map((c) =>
                catEditando?.id === c.id ? (
                  <span key={c.id} className="inline-form">
                    <input
                      value={catEditando.nombre}
                      onChange={(e) =>
                        setCatEditando({ id: c.id, nombre: e.target.value })
                      }
                    />
                    <button className="small" onClick={guardarCategoria}>
                      ✓
                    </button>
                  </span>
                ) : (
                  <span key={c.id} className="chip">
                    {c.nombre}
                    <button
                      className="small ghost"
                      style={{ marginLeft: 6 }}
                      onClick={() =>
                        setCatEditando({ id: c.id, nombre: c.nombre })
                      }
                    >
                      ✎
                    </button>
                  </span>
                )
              )}
            </div>
          </section>

          {/* Formulario para dar de alta un producto nuevo. */}
          <form onSubmit={crearProducto} className="card">
            <h3>Nuevo producto</h3>
            <div className="inline-form">
              {/* Nombre del producto. */}
              <input
                placeholder="Nombre"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                required
              />
              {/* Precio (MoneyInput garantiza un número válido). */}
              <MoneyInput
                placeholder="Precio"
                value={precio}
                onChange={setPrecio}
              />
              {/* Stock inicial. Se guarda como texto y se convierte al enviar. */}
              <input
                placeholder="Stock"
                type="number"
                value={stock}
                onChange={(e) => setStock(e.target.value)}
              />
              {/* Selector de categoría (con opción "Sin categoría"). */}
              <select
                value={categoriaId}
                onChange={(e) => setCategoriaId(e.target.value)}
              >
                <option value="">Sin categoría</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
              {/* Tipo de producto: define cómo se maneja su inventario/receta. */}
              <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
                <option value="comprado">Comprado (se revende)</option>
                <option value="preparado">Preparado (receta de insumos)</option>
                <option value="compuesto">Compuesto (combo)</option>
              </select>
              {/* Input de archivo disfrazado de etiqueta. Está oculto (hidden)
                  y se activa al hacer clic en la etiqueta "Imagen". */}
              <label className="file-label">
                <span className="material-symbols-outlined">image</span>
                Imagen
                <input
                  type="file"
                  accept="image/*"
                  onChange={onImagen}
                  hidden
                />
              </label>
            </div>

            {/* Vista previa de la imagen elegida, si hay alguna. */}
            {imagen && (
              <div className="logo-preview" style={{ marginTop: 12 }}>
                <img src={imagen} alt="Vista previa" />
              </div>
            )}

            <div style={{ marginTop: 12 }}>
              <button type="submit" className="primary">
                Guardar
              </button>
            </div>
            {/* Mensajes de resultado del alta de producto. */}
            {ok && <p className="ok">{ok}</p>}
            {error && <p className="error">{error}</p>}
          </form>
        </>
      )}

      {/* Chips para filtrar la tabla por categoría ("Todos" = sin filtro). */}
      <div className="chips">
        <button
          className={filtroCat === null ? "chip active" : "chip"}
          onClick={() => setFiltroCat(null)}
        >
          Todos
        </button>
        {categorias.map((c) => (
          <button
            key={c.id}
            className={filtroCat === c.id ? "chip active" : "chip"}
            onClick={() => setFiltroCat(c.id)}
          >
            {c.nombre}
          </button>
        ))}
      </div>

      {/* Tabla con el listado de productos visibles. */}
      <table>
        <thead>
          <tr>
            <th></th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Tipo</th>
            <th>Precio</th>
            <th>Stock</th>
            <th>Estado</th>
            {/* Columna de acciones, solo para administradores. */}
            {esAdmin && <th></th>}
          </tr>
        </thead>
        <tbody>
          {visibles.map((p) => (
            <tr key={p.id}>
              <td className="no-label">
                {/* Miniatura del producto o ícono si no tiene imagen. */}
                <span className="cart-thumb">
                  {p.imagen ? (
                    <img src={p.imagen} alt={p.nombre} />
                  ) : (
                    <span className="material-symbols-outlined">image</span>
                  )}
                </span>
              </td>
              <td data-label="Nombre" className="cell-main">
                {p.nombre}
              </td>
              <td data-label="Categoría">{categoriaDe(p.categoria_id)}</td>
              <td data-label="Tipo">{p.tipo}</td>
              <td data-label="Precio">{formatMoney(p.precio)}</td>
              <td data-label="Stock">{p.stock}</td>
              <td data-label="Estado">
                {/* Píldora verde (Activo) o gris (Inactivo). */}
                <span className={p.estado ? "pill on" : "pill off"}>
                  {p.estado ? "Activo" : "Inactivo"}
                </span>
              </td>
              {/* Acciones por producto (solo admin). */}
              {esAdmin && (
                <td className="no-label">
                  <div className="actions">
                    {/* "Receta" solo aparece en productos preparados/compuestos. */}
                    {(p.tipo === "preparado" || p.tipo === "compuesto") && (
                      <button className="ghost" onClick={() => setRecetaDe(p)}>
                        Receta
                      </button>
                    )}
                    {/* "Editar" copia el producto al estado `editando`, lo que
                        abre el modal de edición. */}
                    <button
                      className="ghost"
                      onClick={() =>
                        setEditando({
                          id: p.id,
                          nombre: p.nombre,
                          precio: p.precio,
                          stock: p.stock,
                          categoria_id: p.categoria_id ?? "",
                          imagen: p.imagen,
                          tipo: p.tipo,
                        })
                      }
                    >
                      Editar
                    </button>
                    {/* Alterna entre activo e inactivo. */}
                    <button
                      className="ghost"
                      onClick={() => cambiarEstado(p)}
                    >
                      {p.estado ? "Desactivar" : "Activar"}
                    </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal de edición: solo aparece si hay un producto en `editando`. */}
      {editando && (
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          {/* stopPropagation evita que un clic dentro del modal lo cierre. */}
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar producto</h3>
            {/* Formulario en columna con los campos editables del producto. */}
            <div className="inline-form" style={{ flexDirection: "column", alignItems: "stretch" }}>
              <input
                placeholder="Nombre"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
              <MoneyInput
                placeholder="Precio"
                value={editando.precio}
                onChange={(v) => setEditando({ ...editando, precio: v })}
              />
              <input
                placeholder="Stock"
                type="number"
                value={editando.stock}
                onChange={(e) =>
                  setEditando({ ...editando, stock: Number(e.target.value) })
                }
              />
              {/* Selector de categoría del producto. */}
              <select
                value={editando.categoria_id}
                onChange={(e) =>
                  setEditando({ ...editando, categoria_id: e.target.value })
                }
              >
                <option value="">Sin categoría</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
              {/* Selector de tipo del producto. */}
              <select
                value={editando.tipo}
                onChange={(e) =>
                  setEditando({ ...editando, tipo: e.target.value })
                }
              >
                <option value="comprado">Comprado (se revende)</option>
                <option value="preparado">Preparado (receta de insumos)</option>
                <option value="compuesto">Compuesto (combo)</option>
              </select>
              {/* Cambiar la imagen del producto (usa el compresor). */}
              <label className="file-label">
                <span className="material-symbols-outlined">image</span>
                Cambiar imagen
                <input type="file" accept="image/*" onChange={onImagenEdit} hidden />
              </label>
              {/* Vista previa pequeña de la imagen actual. */}
              {editando.imagen && (
                <div className="logo-preview" style={{ width: 64, height: 64 }}>
                  <img src={editando.imagen} alt="Previa" />
                </div>
              )}
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="ghost" onClick={() => setEditando(null)}>
                Cancelar
              </button>
              <button className="primary" onClick={guardarEdicion}>
                Guardar
              </button>
            </div>
            {/* Error propio del modal de edición. */}
            {error && <p className="error">{error}</p>}
          </div>
        </div>
      )}

      {/* Modal de receta: se abre para preparados/compuestos. Le pasamos el
          producto y recargamos la lista cuando se guarda (onSaved). */}
      {recetaDe && (
        <RecetaModal
          productoId={recetaDe.id}
          productoNombre={recetaDe.nombre}
          productoTipo={recetaDe.tipo}
          onClose={() => setRecetaDe(null)}
          onSaved={cargar}
        />
      )}
    </div>
  );
}
