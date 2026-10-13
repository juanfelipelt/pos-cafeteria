/*
 * ============================================================================
 * PÁGINA: Pizarra
 * ============================================================================
 * ¿Qué es este archivo?
 *   Es el tablero de comunicación interna del equipo. Aquí los empleados
 *   dejan NOTAS y TAREAS para todos, para el admin o para los cajeros.
 *   Las tareas se pueden marcar como hechas y cualquier nota se puede
 *   archivar o eliminar.
 *
 * ¿Para qué sirve?
 *   Reemplaza el "papelito pegado en la pared": todo el equipo ve los
 *   pendientes y los mensajes importantes en un solo lugar.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Usa `api` (../api) para listar, crear, actualizar y borrar notas.
 *   - Usa `eventSourceUrl` y `getToken` para abrir un canal EN VIVO
 *     (EventSource / Server-Sent Events) con el backend: si otro usuario
 *     crea o cambia una nota, esta pantalla se actualiza sola sin recargar.
 *   - Usa `useAuth` (../auth) para saber quién eres y decidir si puedes
 *     editar una nota (el autor o un administrador).
 * ============================================================================
 */

import { useCallback, useEffect, useState } from "react";
import { api, eventSourceUrl, getToken } from "../api";
import { useAuth } from "../auth";

// Representa una nota o tarea tal como la devuelve el backend.
interface Nota {
  id: string; // Identificador único.
  texto: string; // Contenido del mensaje.
  tipo: string; // "nota" o "tarea".
  destinatario: string; // "todos", "admin" o "cajero".
  prioridad: string; // "normal" o "alta".
  autor_id: string | null; // Quién la creó (null si el autor fue borrado).
  autor_nombre: string; // Nombre del autor para mostrar.
  fecha_creacion: string; // Fecha/hora en formato ISO.
  hecho: boolean; // Solo para tareas: si ya se completó.
  archivada: boolean; // Si está oculta del tablero principal.
}

// Tipos de eventos que nos interesan del canal en vivo. Cuando llega uno
// de estos, volvemos a cargar las notas para reflejar el cambio al instante.
const EVENTOS = ["nota_creada", "nota_actualizada", "nota_eliminada"];

// Opciones de "a quién va dirigida" la nota. `v` es el valor real que se
// envía al backend y `label` el texto amigable que ve el usuario.
const DESTINATARIOS = [
  { v: "todos", label: "Todos" },
  { v: "admin", label: "Admin" },
  { v: "cajero", label: "Cajero" },
];

// Convierte una fecha ISO en un texto corto y legible para el usuario,
// por ejemplo "12/10, 14:30". Se adapta al idioma del navegador.
function cuando(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Pizarra() {
  // Usuario en sesión: se usa para saber si puede editar cada nota.
  const { user } = useAuth();

  // ------------------------------ ESTADO ---------------------------------
  const [notas, setNotas] = useState<Nota[]>([]); // Todas las notas cargadas.
  const [filtroDest, setFiltroDest] = useState(""); // Filtro por destinatario ("" = todas).
  const [verArchivadas, setVerArchivadas] = useState(false); // Mostrar u ocultar archivadas.

  // Campos del formulario para crear una nota/tarea nueva.
  const [texto, setTexto] = useState("");
  const [tipo, setTipo] = useState("nota");
  const [destinatario, setDestinatario] = useState("todos");
  const [prioridad, setPrioridad] = useState("normal");

  // Edición en línea: guardamos el id de la nota que se edita y su texto.
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [editTexto, setEditTexto] = useState("");
  const [error, setError] = useState(""); // Mensaje de error.

  // Trae las notas del backend aplicando los filtros activos. Se envuelve
  // en useCallback para que su identidad solo cambie cuando cambie algún
  // filtro; así los useEffect que la usan no se disparan de más.
  const cargar = useCallback(async () => {
    // Construimos los parámetros de la URL solo si hay algo que filtrar.
    const params = new URLSearchParams();
    if (filtroDest) params.set("destinatario", filtroDest);
    if (verArchivadas) params.set("incluir_archivadas", "true");
    const qs = params.toString();
    // Si hay parámetros, se agregan como "?clave=valor".
    setNotas(await api<Nota[]>(`/notas${qs ? `?${qs}` : ""}`));
  }, [filtroDest, verArchivadas]);

  // EFECTO: recarga las notas cada vez que cambia el filtro (cargar cambia).
  useEffect(() => {
    cargar().catch((err) =>
      setError(err instanceof Error ? err.message : "Error")
    );
  }, [cargar]);

  // EFECTO: abre el canal en vivo (Server-Sent Events) con el backend.
  // Cada vez que llega un evento relevante, recargamos las notas.
  useEffect(() => {
    const es = new EventSource(
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as { type: string };
      if (EVENTOS.includes(msg.type)) cargar();
    };
    // Al desmontar la pantalla cerramos la conexión para no dejarla colgada.
    return () => es.close();
  }, [cargar]);

  // Crea una nota o tarea nueva a partir del formulario.
  async function agregar(e: React.FormEvent) {
    e.preventDefault(); // Evita que el navegador recargue la página.
    if (!texto.trim()) return; // No permitimos notas vacías.
    setError("");
    try {
      await api("/notas", {
        method: "POST",
        body: JSON.stringify({ texto, tipo, destinatario, prioridad }),
      });
      // Limpiamos el formulario dejándolo en sus valores por defecto.
      setTexto("");
      setTipo("nota");
      setDestinatario("todos");
      setPrioridad("normal");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  // Marca/desmarca una tarea como hecha (PATCH = actualización parcial).
  async function toggleHecho(n: Nota) {
    await api(`/notas/${n.id}`, {
      method: "PATCH",
      body: JSON.stringify({ hecho: !n.hecho }), // Invertimos el valor actual.
    });
    await cargar();
  }

  // Archiva o desarchiva una nota (la oculta/muestra del tablero).
  async function archivar(n: Nota) {
    await api(`/notas/${n.id}`, {
      method: "PATCH",
      body: JSON.stringify({ archivada: !n.archivada }),
    });
    await cargar();
  }

  // Guarda el texto editado de una nota y cierra el modo edición.
  async function guardarEdicion(n: Nota) {
    await api(`/notas/${n.id}`, {
      method: "PATCH",
      body: JSON.stringify({ texto: editTexto }),
    });
    setEditandoId(null);
    await cargar();
  }

  // Elimina una nota, pidiendo confirmación antes por seguridad.
  async function eliminar(n: Nota) {
    if (!window.confirm("¿Eliminar esta nota?")) return;
    await api(`/notas/${n.id}`, { method: "DELETE" });
    await cargar();
  }

  // Regla de permisos: puede editar quien sea admin, o quien sea el autor.
  const puedeEditar = (n: Nota) =>
    user?.rol === "admin" || user?.id === n.autor_id;

  // Separamos las notas en dos columnas: tareas y el resto (notas).
  const tareas = notas.filter((n) => n.tipo === "tarea");
  const notitas = notas.filter((n) => n.tipo !== "tarea");

  // Dibuja UNA tarjeta de nota/tarea. Recibe la nota y devuelve su JSX.
  function tarjeta(n: Nota) {
    return (
      // Las clases cambian según el estado: archivada, hecha o prioridad alta.
      <div
        key={n.id}
        className={`note-card${n.archivada ? " archivada" : ""}${
          n.hecho ? " done" : ""
        }${n.prioridad === "alta" ? " alta" : ""}`}
      >
        {/* Solo las tareas tienen casilla para marcar como hecha. */}
        {n.tipo === "tarea" && (
          <button
            className="note-check"
            onClick={() => toggleHecho(n)}
            aria-label="Marcar hecha"
          >
            {/* El ícono cambia según si está hecha o no. */}
            <span className="material-symbols-outlined">
              {n.hecho ? "check_box" : "check_box_outline_blank"}
            </span>
          </button>
        )}

        <div className="note-body">
          {/* Si esta nota se está editando, mostramos un input; si no, el texto. */}
          {editandoId === n.id ? (
            <div className="note-edit">
              <input
                value={editTexto}
                onChange={(e) => setEditTexto(e.target.value)}
                autoFocus
              />
              {/* ✓ guarda, ✕ cancela la edición. */}
              <button className="small" onClick={() => guardarEdicion(n)}>
                ✓
              </button>
              <button
                className="small ghost"
                onClick={() => setEditandoId(null)}
              >
                ✕
              </button>
            </div>
          ) : (
            <div className="note-text">{n.texto}</div>
          )}

          {/* Pie de la tarjeta con la información de la nota. */}
          <div className="note-meta">
            {/* Etiqueta "Alta" solo si la prioridad es alta. */}
            {n.prioridad === "alta" && <span className="prio">Alta</span>}
            <span
              className="dest"
              title={`Dirigida a ${n.destinatario}`}
            >
              {/* Texto amigable según el destinatario. */}
              {n.destinatario === "todos" ? "Todos" : `Para ${n.destinatario}`}
            </span>
            <span className="who">
              {/* Autor + fecha formateada (o "—" si no hay autor). */}
              {n.autor_nombre || "—"} · {cuando(n.fecha_creacion)}
            </span>
            {/* Aviso adicional si la nota está archivada. */}
            {n.archivada && <span className="tag-arch">Archivada</span>}
          </div>
        </div>

        {/* Botonera: solo aparece si el usuario tiene permiso para editar. */}
        {puedeEditar(n) && (
          <div className="note-actions">
            {/* El botón de editar solo se muestra si NO estamos editando ya. */}
            {editandoId !== n.id && (
              <button
                className="ghost small"
                title="Editar"
                onClick={() => {
                  setEditandoId(n.id);
                  setEditTexto(n.texto); // Cargamos el texto actual en el input.
                }}
              >
                <span className="material-symbols-outlined">edit</span>
              </button>
            )}
            {/* Archivar/desarchivar la nota. */}
            <button
              className="ghost small"
              title={n.archivada ? "Desarchivar" : "Archivar"}
              onClick={() => archivar(n)}
            >
              <span className="material-symbols-outlined">archive</span>
            </button>
            {/* Eliminar la nota. */}
            <button
              className="ghost small danger"
              title="Eliminar"
              onClick={() => eliminar(n)}
            >
              <span className="material-symbols-outlined">delete</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <h2>Pizarra</h2>
      {/* Mostramos el mensaje de error si existe. */}
      {error && <p className="error">{error}</p>}

      {/* Formulario para escribir una nota o tarea nueva. */}
      <form onSubmit={agregar} className="card note-add">
        <textarea
          placeholder="Escribe una nota o tarea..."
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          rows={2}
        />
        <div className="note-add-bar">
          {/* Botones tipo "chip" para elegir Nota o Tarea. */}
          <div className="chips">
            <button
              type="button"
              className={tipo === "nota" ? "chip active" : "chip"}
              onClick={() => setTipo("nota")}
            >
              Nota
            </button>
            <button
              type="button"
              className={tipo === "tarea" ? "chip active" : "chip"}
              onClick={() => setTipo("tarea")}
            >
              Tarea
            </button>
          </div>

          {/* Selector de destinatario generado a partir de DESTINATARIOS. */}
          <select
            value={destinatario}
            onChange={(e) => setDestinatario(e.target.value)}
          >
            {DESTINATARIOS.map((d) => (
              <option key={d.v} value={d.v}>
                Para {d.label}
              </option>
            ))}
          </select>

          {/* Chip de prioridad: al pulsarlo alterna entre alta y normal. */}
          <button
            type="button"
            className={prioridad === "alta" ? "chip active prio-chip" : "chip"}
            onClick={() =>
              setPrioridad(prioridad === "alta" ? "normal" : "alta")
            }
          >
            Alta
          </button>

          <button type="submit" className="primary">
            Agregar
          </button>
        </div>
      </form>

      {/* Barra de filtros: por destinatario y ver archivadas. */}
      <div className="note-filtros">
        <div className="chips">
          <button
            className={filtroDest === "" ? "chip active" : "chip"}
            onClick={() => setFiltroDest("")}
          >
            Todo
          </button>
          {/* Un botón de filtro por cada destinatario posible. */}
          {DESTINATARIOS.map((d) => (
            <button
              key={d.v}
              className={filtroDest === d.v ? "chip active" : "chip"}
              onClick={() => setFiltroDest(d.v)}
            >
              {d.label}
            </button>
          ))}
        </div>
        {/* Casilla para incluir o no las notas archivadas. */}
        <label className="arch-toggle">
          <input
            type="checkbox"
            checked={verArchivadas}
            onChange={(e) => setVerArchivadas(e.target.checked)}
          />
          Ver archivadas
        </label>
      </div>

      {/* Tablero con dos columnas: Tareas y Notas. */}
      <div className="board">
        {/* Columna de tareas. */}
        <section className="card board-col">
          <h3>Tareas</h3>
          {tareas.length === 0 ? (
            <p className="muted">Sin tareas.</p>
          ) : (
            tareas.map(tarjeta) // Reutilizamos la función `tarjeta`.
          )}
        </section>

        {/* Columna de notas (todo lo que no es tarea). */}
        <section className="card board-col">
          <h3>Notas</h3>
          {notitas.length === 0 ? (
            <p className="muted">Sin notas.</p>
          ) : (
            notitas.map(tarjeta)
          )}
        </section>
      </div>
    </div>
  );
}
