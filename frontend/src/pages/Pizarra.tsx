import { useCallback, useEffect, useState } from "react";
import { api, eventSourceUrl, getToken } from "../api";
import { useAuth } from "../auth";

interface Nota {
  id: string;
  texto: string;
  tipo: string;
  destinatario: string;
  prioridad: string;
  autor_id: string | null;
  autor_nombre: string;
  fecha_creacion: string;
  hecho: boolean;
  archivada: boolean;
}

const EVENTOS = ["nota_creada", "nota_actualizada", "nota_eliminada"];

const DESTINATARIOS = [
  { v: "todos", label: "Todos" },
  { v: "admin", label: "Admin" },
  { v: "cajero", label: "Cajero" },
];

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
  const { user } = useAuth();

  const [notas, setNotas] = useState<Nota[]>([]);
  const [filtroDest, setFiltroDest] = useState("");
  const [verArchivadas, setVerArchivadas] = useState(false);

  const [texto, setTexto] = useState("");
  const [tipo, setTipo] = useState("nota");
  const [destinatario, setDestinatario] = useState("todos");
  const [prioridad, setPrioridad] = useState("normal");

  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [editTexto, setEditTexto] = useState("");
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    const params = new URLSearchParams();
    if (filtroDest) params.set("destinatario", filtroDest);
    if (verArchivadas) params.set("incluir_archivadas", "true");
    const qs = params.toString();
    setNotas(await api<Nota[]>(`/notas${qs ? `?${qs}` : ""}`));
  }, [filtroDest, verArchivadas]);

  useEffect(() => {
    cargar().catch((err) =>
      setError(err instanceof Error ? err.message : "Error")
    );
  }, [cargar]);

  useEffect(() => {
    const es = new EventSource(
      eventSourceUrl(`/eventos/stream?token=${getToken() ?? ""}`)
    );
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as { type: string };
      if (EVENTOS.includes(msg.type)) cargar();
    };
    return () => es.close();
  }, [cargar]);

  async function agregar(e: React.FormEvent) {
    e.preventDefault();
    if (!texto.trim()) return;
    setError("");
    try {
      await api("/notas", {
        method: "POST",
        body: JSON.stringify({ texto, tipo, destinatario, prioridad }),
      });
      setTexto("");
      setTipo("nota");
      setDestinatario("todos");
      setPrioridad("normal");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function toggleHecho(n: Nota) {
    await api(`/notas/${n.id}`, {
      method: "PATCH",
      body: JSON.stringify({ hecho: !n.hecho }),
    });
    await cargar();
  }

  async function archivar(n: Nota) {
    await api(`/notas/${n.id}`, {
      method: "PATCH",
      body: JSON.stringify({ archivada: !n.archivada }),
    });
    await cargar();
  }

  async function guardarEdicion(n: Nota) {
    await api(`/notas/${n.id}`, {
      method: "PATCH",
      body: JSON.stringify({ texto: editTexto }),
    });
    setEditandoId(null);
    await cargar();
  }

  async function eliminar(n: Nota) {
    if (!window.confirm("¿Eliminar esta nota?")) return;
    await api(`/notas/${n.id}`, { method: "DELETE" });
    await cargar();
  }

  const puedeEditar = (n: Nota) =>
    user?.rol === "admin" || user?.id === n.autor_id;

  const tareas = notas.filter((n) => n.tipo === "tarea");
  const notitas = notas.filter((n) => n.tipo !== "tarea");

  function tarjeta(n: Nota) {
    return (
      <div
        key={n.id}
        className={`note-card${n.archivada ? " archivada" : ""}${
          n.hecho ? " done" : ""
        }${n.prioridad === "alta" ? " alta" : ""}`}
      >
        {n.tipo === "tarea" && (
          <button
            className="note-check"
            onClick={() => toggleHecho(n)}
            aria-label="Marcar hecha"
          >
            <span className="material-symbols-outlined">
              {n.hecho ? "check_box" : "check_box_outline_blank"}
            </span>
          </button>
        )}

        <div className="note-body">
          {editandoId === n.id ? (
            <div className="note-edit">
              <input
                value={editTexto}
                onChange={(e) => setEditTexto(e.target.value)}
                autoFocus
              />
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

          <div className="note-meta">
            {n.prioridad === "alta" && <span className="prio">Alta</span>}
            <span
              className="dest"
              title={`Dirigida a ${n.destinatario}`}
            >
              {n.destinatario === "todos" ? "Todos" : `Para ${n.destinatario}`}
            </span>
            <span className="who">
              {n.autor_nombre || "—"} · {cuando(n.fecha_creacion)}
            </span>
            {n.archivada && <span className="tag-arch">Archivada</span>}
          </div>
        </div>

        {puedeEditar(n) && (
          <div className="note-actions">
            {editandoId !== n.id && (
              <button
                className="ghost small"
                title="Editar"
                onClick={() => {
                  setEditandoId(n.id);
                  setEditTexto(n.texto);
                }}
              >
                <span className="material-symbols-outlined">edit</span>
              </button>
            )}
            <button
              className="ghost small"
              title={n.archivada ? "Desarchivar" : "Archivar"}
              onClick={() => archivar(n)}
            >
              <span className="material-symbols-outlined">archive</span>
            </button>
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
      {error && <p className="error">{error}</p>}

      <form onSubmit={agregar} className="card note-add">
        <textarea
          placeholder="Escribe una nota o tarea..."
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          rows={2}
        />
        <div className="note-add-bar">
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

      <div className="note-filtros">
        <div className="chips">
          <button
            className={filtroDest === "" ? "chip active" : "chip"}
            onClick={() => setFiltroDest("")}
          >
            Todo
          </button>
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
        <label className="arch-toggle">
          <input
            type="checkbox"
            checked={verArchivadas}
            onChange={(e) => setVerArchivadas(e.target.checked)}
          />
          Ver archivadas
        </label>
      </div>

      <div className="board">
        <section className="card board-col">
          <h3>Tareas</h3>
          {tareas.length === 0 ? (
            <p className="muted">Sin tareas.</p>
          ) : (
            tareas.map(tarjeta)
          )}
        </section>

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
