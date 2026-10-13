/*
 * ARCHIVO: src/pages/Proveedores.tsx
 * -----------------------------------------------------------------------------
 * ¿Qué es?
 *   Pantalla (página) "Proveedores" de Cafetería POS, el sistema de gestión de la
 *   cafetería. Aquí se administra el listado de proveedores: las empresas o
 *   personas a las que el negocio les compra productos e insumos.
 *
 * ¿Para qué sirve?
 *   - Mostrar la tabla de proveedores con su nombre, identificación, contacto,
 *     teléfono, email y estado (activo/inactivo).
 *   - Permitir al administrador crear un proveedor nuevo con un formulario.
 *   - Permitir al administrador editar un proveedor en una ventana modal,
 *     activarlo/desactivarlo y eliminarlo.
 *   Los usuarios que no son admin sólo pueden ver la lista.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Se monta como ruta "/proveedores" dentro de <App /> (App.tsx), protegida
 *     por login y envuelta por <Layout />.
 *   - Usa {api} (src/api.ts) para hablar con el backend.
 *   - Usa {useAuth} (src/auth.tsx) para saber el rol (admin o no).
 *   - Los proveedores creados aquí se usan luego en Insumos (para asociar un
 *     proveedor a cada materia prima) y en Compras (para registrar a quién se
 *     le compró).
 * -----------------------------------------------------------------------------
 */

// --- Importaciones -----------------------------------------------------------
import { useEffect, useState } from "react"; // Hooks de React: efectos y estado.
import { api } from "../api"; // Cliente HTTP que agrega el token de sesión.
import { useAuth } from "../auth"; // Hook para saber el usuario y su rol.

// Lista fija de tipos de identificación válidos en Colombia (y otros documentos).
const TIPOS_IDENTIFICACION = [
  "CC", // Cédula de ciudadanía.
  "NIT", // Número de identificación tributaria (empresas).
  "CE", // Cédula de extranjería.
  "TI", // Tarjeta de identidad.
  "PPT", // Permiso por protección temporal.
  "PASAPORTE",
  "OTRO",
];

// --- Tipos de datos ----------------------------------------------------------

// Un proveedor tal como lo devuelve el backend.
interface Proveedor {
  id: string;
  nombre: string;
  contacto: string; // Nombre de la persona de contacto.
  telefono: string;
  email: string;
  direccion: string;
  tipo_identificacion: string; // Ej. "NIT".
  identificacion: string; // Número del documento.
  estado: boolean; // true = activo, false = inactivo.
}

// Copia del proveedor que se está editando en el modal.
// No incluye "estado" porque el estado se cambia con un botón aparte, no en el formulario.
interface Editando {
  id: string;
  nombre: string;
  contacto: string;
  telefono: string;
  email: string;
  direccion: string;
  tipo_identificacion: string;
  identificacion: string;
}

// Componente principal de la página.
export default function Proveedores() {
  const { user } = useAuth(); // Usuario logueado (para permisos por rol).

  // --- Estados con las listas y el formulario ---
  const [proveedores, setProveedores] = useState<Proveedor[]>([]); // Lista de proveedores.
  const [nombre, setNombre] = useState(""); // Campo nombre del formulario de creación.
  const [contacto, setContacto] = useState(""); // Campo contacto.
  const [telefono, setTelefono] = useState(""); // Campo teléfono.
  const [email, setEmail] = useState(""); // Campo email.
  const [tipoId, setTipoId] = useState(""); // Tipo de identificación elegido.
  const [identificacion, setIdentificacion] = useState(""); // Número de identificación.
  const [editando, setEditando] = useState<Editando | null>(null); // Proveedor en edición (null = modal cerrado).
  const [error, setError] = useState(""); // Mensaje de error.
  const [ok, setOk] = useState(""); // Mensaje de éxito.

  // Trae la lista de proveedores desde el backend y la guarda en el estado.
  async function cargar() {
    setProveedores(await api<Proveedor[]>("/proveedores"));
  }

  // Al montar la página, cargamos los datos una sola vez.
  useEffect(() => {
    cargar();
  }, []);

  // Maneja el envío del formulario de creación de proveedor.
  async function crear(e: React.FormEvent) {
    e.preventDefault(); // Evita la recarga de página por defecto del formulario.
    setError("");
    setOk("");
    try {
      // POST al backend con los datos del nuevo proveedor.
      await api("/proveedores", {
        method: "POST",
        body: JSON.stringify({
          nombre,
          contacto,
          telefono,
          email,
          tipo_identificacion: tipoId,
          identificacion,
        }),
      });
      // Limpiamos todos los campos del formulario.
      setNombre("");
      setContacto("");
      setTelefono("");
      setEmail("");
      setTipoId("");
      setIdentificacion("");
      setOk("Proveedor creado.");
      await cargar(); // Refrescamos la tabla.
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Guarda los cambios del proveedor que se está editando en el modal.
  async function guardarEdicion() {
    if (!editando) return; // Sin proveedor en edición no hay nada que guardar.
    setError("");
    try {
      // PUT con el id del proveedor y sus nuevos datos.
      await api(`/proveedores/${editando.id}`, {
        method: "PUT",
        body: JSON.stringify({
          nombre: editando.nombre,
          contacto: editando.contacto,
          telefono: editando.telefono,
          email: editando.email,
          direccion: editando.direccion,
          tipo_identificacion: editando.tipo_identificacion,
          identificacion: editando.identificacion,
        }),
      });
      setEditando(null); // Cerramos el modal.
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Activa o desactiva un proveedor (envía el valor contrario al estado actual).
  async function cambiarEstado(p: Proveedor) {
    await api(`/proveedores/${p.id}/estado`, {
      method: "PATCH", // PATCH porque cambiamos sólo el campo "estado".
      body: JSON.stringify({ estado: !p.estado }),
    });
    await cargar();
  }

  // Elimina un proveedor, previa confirmación del usuario.
  async function eliminar(id: string) {
    if (!window.confirm("¿Eliminar este proveedor?")) return;
    setError("");
    try {
      await api(`/proveedores/${id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Devuelve la identificación ya formateada, por ejemplo "NIT 900123456",
  // o "—" si el proveedor no tiene datos de identificación.
  const ident = (p: Proveedor) =>
    p.identificacion ? `${p.tipo_identificacion || "—"} ${p.identificacion}` : "—";

  // --- Render de la pantalla (JSX) -------------------------------------------
  return (
    <div>
      <h2>Proveedores</h2>

      {/* Mensaje de error general */}
      {error && <p className="error">{error}</p>}

      {/* Formulario de creación: sólo visible para administradores */}
      {user?.rol === "admin" && (
        <form onSubmit={crear} className="card">
          <h3>Nuevo proveedor</h3>
        <div className="inline-form">
          {/* Desplegable de tipo de identificación (la opción inicial está deshabilitada) */}
          <select value={tipoId} onChange={(e) => setTipoId(e.target.value)}>
            <option value="" disabled>
              Tipo identificación
            </option>
            {TIPOS_IDENTIFICACION.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          {/* Número de identificación */}
          <input
            placeholder="N° identificación"
            value={identificacion}
            onChange={(e) => setIdentificacion(e.target.value)}
          />
          {/* Nombre del proveedor (obligatorio) */}
          <input
            placeholder="Nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
          />
          {/* Persona de contacto (obligatorio) */}
          <input
            placeholder="Contacto"
            value={contacto}
            onChange={(e) => setContacto(e.target.value)}
            required
          />
          {/* Teléfono (obligatorio) */}
          <input
            placeholder="Teléfono"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            required
          />
          {/* Email (opcional; el navegador valida su formato) */}
          <input
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button type="submit" className="primary">
            Agregar
          </button>
        </div>
        {ok && <p className="ok">{ok}</p>}
      </form>
      )}

      {/* Tabla con todos los proveedores */}
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Identificación</th>
            <th>Contacto</th>
            <th>Teléfono</th>
            <th>Email</th>
            <th>Estado</th>
            {/* Columna de acciones sólo para admin */}
            {user?.rol === "admin" && <th></th>}
          </tr>
        </thead>
        <tbody>
          {/* Una fila por cada proveedor */}
          {proveedores.map((p) => (
            <tr key={p.id}>
              <td data-label="Nombre" className="cell-main">
                {p.nombre}
              </td>
              <td data-label="Identificación">{ident(p)}</td>
              <td data-label="Contacto">{p.contacto}</td>
              <td data-label="Teléfono">{p.telefono}</td>
              {/* Si no hay email mostramos "—" */}
              <td data-label="Email">{p.email || "—"}</td>
              <td data-label="Estado">
                {/* Píldora que cambia de color según el estado */}
                <span className={p.estado ? "pill on" : "pill off"}>
                  {p.estado ? "Activo" : "Inactivo"}
                </span>
              </td>
              {/* Celda de acciones sólo para admin */}
              {user?.rol === "admin" && (
                <td className="no-label">
                  <div className="actions">
                    {/* Abre el modal copiando los datos del proveedor al estado "editando" */}
                    <button
                      className="ghost"
                      onClick={() =>
                        setEditando({
                          id: p.id,
                          nombre: p.nombre,
                          contacto: p.contacto,
                          telefono: p.telefono,
                          email: p.email,
                          direccion: p.direccion,
                          tipo_identificacion: p.tipo_identificacion,
                          identificacion: p.identificacion,
                        })
                      }
                    >
                      Editar
                    </button>
                    {/* El texto cambia según el estado actual */}
                    <button
                      className="ghost"
                      onClick={() => cambiarEstado(p)}
                    >
                      {p.estado ? "Desactivar" : "Activar"}
                    </button>
                    <button
                      className="ghost danger"
                      onClick={() => eliminar(p.id)}
                    >
                      Eliminar
                    </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal de edición: sólo se dibuja si "editando" tiene datos */}
      {editando && (
        // Clic en el fondo oscuro cierra el modal
        <div className="modal-overlay" onClick={() => setEditando(null)}>
          {/* stopPropagation evita que un clic dentro del modal lo cierre */}
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Editar proveedor</h3>
            <div className="inline-form" style={{ flexDirection: "column", alignItems: "stretch" }}>
              {/* Cada campo actualiza una copia del proveedor con setEditando({...editando, campo}) */}
              <select
                value={editando.tipo_identificacion}
                onChange={(e) =>
                  setEditando({ ...editando, tipo_identificacion: e.target.value })
                }
              >
                <option value="" disabled>
                  Tipo identificación
                </option>
                {TIPOS_IDENTIFICACION.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <input
                placeholder="N° identificación"
                value={editando.identificacion}
                onChange={(e) =>
                  setEditando({ ...editando, identificacion: e.target.value })
                }
              />
              <input
                placeholder="Nombre"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
              <input
                placeholder="Contacto"
                value={editando.contacto}
                onChange={(e) =>
                  setEditando({ ...editando, contacto: e.target.value })
                }
              />
              <input
                placeholder="Teléfono"
                value={editando.telefono}
                onChange={(e) =>
                  setEditando({ ...editando, telefono: e.target.value })
                }
              />
              <input
                placeholder="Email"
                value={editando.email}
                onChange={(e) =>
                  setEditando({ ...editando, email: e.target.value })
                }
              />
              <input
                placeholder="Dirección"
                value={editando.direccion}
                onChange={(e) =>
                  setEditando({ ...editando, direccion: e.target.value })
                }
              />
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
