import { useEffect, useState } from "react";
import { api } from "../api";
import MoneyInput from "../components/MoneyInput";
import { useAuth } from "../auth";
import { formatMoney } from "../lib/format";

interface Categoria {
  id: string;
  nombre: string;
  descripcion: string;
  estado: boolean;
}

interface Producto {
  id: string;
  nombre: string;
  descripcion: string;
  categoria_id: string | null;
  imagen: string;
  precio: number;
  stock: number;
  estado: boolean;
}

interface Editando {
  id: string;
  nombre: string;
  precio: number;
  stock: number;
  categoria_id: string;
  imagen: string;
}

export default function Productos() {
  const { user } = useAuth();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);

  const [nombre, setNombre] = useState("");
  const [precio, setPrecio] = useState(0);
  const [stock, setStock] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [imagen, setImagen] = useState("");

  const [nuevaCategoria, setNuevaCategoria] = useState("");
  const [catEditando, setCatEditando] = useState<{ id: string; nombre: string } | null>(null);

  const [editando, setEditando] = useState<Editando | null>(null);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [filtroCat, setFiltroCat] = useState<string | null>(null);

  const esAdmin = user?.rol === "admin";

  async function cargar() {
    const [ps, cs] = await Promise.all([
      api<Producto[]>("/productos"),
      api<Categoria[]>("/categorias"),
    ]);
    setProductos(ps);
    setCategorias(cs);
  }

  useEffect(() => {
    cargar();
  }, []);

  function onImagen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImagen(reader.result as string);
    reader.readAsDataURL(file);
  }

  function onImagenEdit(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !editando) return;
    const reader = new FileReader();
    reader.onload = () =>
      setEditando({ ...editando, imagen: reader.result as string });
    reader.readAsDataURL(file);
  }

  async function crearCategoria(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/categorias", {
        method: "POST",
        body: JSON.stringify({ nombre: nuevaCategoria }),
      });
      setNuevaCategoria("");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function guardarCategoria() {
    if (!catEditando) return;
    await api(`/categorias/${catEditando.id}`, {
      method: "PUT",
      body: JSON.stringify({ nombre: catEditando.nombre }),
    });
    setCatEditando(null);
    await cargar();
  }

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
          stock: Number(stock) || 0,
          categoria_id: categoriaId || null,
          imagen,
        }),
      });
      setNombre("");
      setPrecio(0);
      setStock("");
      setCategoriaId("");
      setImagen("");
      setOk("Producto creado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

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
        }),
      });
      setEditando(null);
      setOk("Producto actualizado.");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function cambiarEstado(p: Producto) {
    await api(`/productos/${p.id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: !p.estado }),
    });
    await cargar();
  }

  const categoriaDe = (id: string | null) =>
    categorias.find((c) => c.id === id)?.nombre ?? "—";

  const visibles = filtroCat
    ? productos.filter((p) => p.categoria_id === filtroCat)
    : productos;

  return (
    <div>
      <h2>Productos</h2>

      {esAdmin && (
        <>
          <section className="card">
            <h3>Categorías</h3>
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

          <form onSubmit={crearProducto} className="card">
            <h3>Nuevo producto</h3>
            <div className="inline-form">
              <input
                placeholder="Nombre"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                required
              />
              <MoneyInput
                placeholder="Precio"
                value={precio}
                onChange={setPrecio}
              />
              <input
                placeholder="Stock"
                type="number"
                value={stock}
                onChange={(e) => setStock(e.target.value)}
              />
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
            {ok && <p className="ok">{ok}</p>}
            {error && <p className="error">{error}</p>}
          </form>
        </>
      )}

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

      <table>
        <thead>
          <tr>
            <th></th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Precio</th>
            <th>Stock</th>
            <th>Estado</th>
            {esAdmin && <th></th>}
          </tr>
        </thead>
        <tbody>
          {visibles.map((p) => (
            <tr key={p.id}>
              <td className="no-label">
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
              <td data-label="Precio">{formatMoney(p.precio)}</td>
              <td data-label="Stock">{p.stock}</td>
              <td data-label="Estado">
                <span className={p.estado ? "pill on" : "pill off"}>
                  {p.estado ? "Activo" : "Inactivo"}
                </span>
              </td>
              {esAdmin && (
                <td className="no-label">
                  <div className="actions">
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
                        })
                      }
                    >
                      Editar
                    </button>
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

      {editando && (
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar producto</h3>
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
              <label className="file-label">
                <span className="material-symbols-outlined">image</span>
                Cambiar imagen
                <input type="file" accept="image/*" onChange={onImagenEdit} hidden />
              </label>
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
            {error && <p className="error">{error}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
