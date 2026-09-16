import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useConfig } from "../config";
import { comprimirImagen } from "../lib/image";

const DIAS = [
  { n: 1, label: "Lun" },
  { n: 2, label: "Mar" },
  { n: 3, label: "Mié" },
  { n: 4, label: "Jue" },
  { n: 5, label: "Vie" },
  { n: 6, label: "Sáb" },
  { n: 7, label: "Dom" },
];

export default function Configuracion() {
  const { user } = useAuth();
  const { logo, refresh } = useConfig();
  const [preview, setPreview] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const [dias, setDias] = useState<number[]>([1, 2, 3, 4, 5, 6]);
  const [mensajeDias, setMensajeDias] = useState("");

  useEffect(() => {
    api<Record<string, string>>("/configuracion")
      .then((data) => {
        if (data.dias_laborales) {
          const nums = data.dias_laborales
            .split(",")
            .map((x) => Number(x.trim()))
            .filter((n) => n >= 1 && n <= 7);
          if (nums.length) setDias(nums);
        }
      })
      .catch(() => {});
  }, []);

  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  function toggleDia(n: number) {
    setDias((prev) =>
      prev.includes(n) ? prev.filter((d) => d !== n) : [...prev, n].sort()
    );
    setMensajeDias("");
  }

  async function guardarDias() {
    setError("");
    setMensajeDias("");
    try {
      await api("/configuracion/dias_laborales", {
        method: "PUT",
        body: JSON.stringify({ valor: dias.join(",") }),
      });
      setMensajeDias("Días laborables actualizados.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setPreview(await comprimirImagen(file, { maxSize: 400 }));
    } catch {
      setError("No se pudo procesar la imagen.");
    }
  }

  async function guardar() {
    if (!preview) return;
    setError("");
    setMensaje("");
    try {
      await api("/configuracion/logo", {
        method: "PUT",
        body: JSON.stringify({ logo: preview }),
      });
      await refresh();
      setPreview(null);
      setMensaje("Logo actualizado correctamente.");
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  }

  return (
    <div>
      <h2>Configuración</h2>

      <section className="card">
        <h3>Logo</h3>
        <p className="muted">
          Este logo aparece en el menú lateral y en la pantalla de inicio de
          sesión.
        </p>

        <div className="logo-editor">
          <div className="logo-preview">
            {preview ? (
              <img src={preview} alt="Vista previa" />
            ) : logo ? (
              <img src={logo} alt="Logo actual" />
            ) : (
              <span className="logo-placeholder">Cafetería POS</span>
            )}
          </div>

          <div className="logo-actions">
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={onFile}
              hidden
            />
            <button type="button" onClick={() => fileRef.current?.click()}>
              Elegir imagen
            </button>
            <button
              type="button"
              className="ghost"
              disabled={!preview}
              onClick={guardar}
            >
              Guardar
            </button>
          </div>
        </div>

        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="card">
        <h3>Días laborables</h3>
        <p className="muted">
          Se usan para repartir los costos fijos mensuales entre los días que
          trabajas (punto de equilibrio y utilidad diaria).
        </p>
        <div className="chips" style={{ marginTop: 12 }}>
          {DIAS.map((d) => (
            <button
              key={d.n}
              type="button"
              className={dias.includes(d.n) ? "chip active" : "chip"}
              onClick={() => toggleDia(d.n)}
            >
              {d.label}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 12 }}>
          <button type="button" className="primary" onClick={guardarDias}>
            Guardar días
          </button>
        </div>
        {mensajeDias && <p className="ok">{mensajeDias}</p>}
      </section>
    </div>
  );
}
