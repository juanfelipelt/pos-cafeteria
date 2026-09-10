import { useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useConfig } from "../config";
import { comprimirImagen } from "../lib/image";

export default function Configuracion() {
  const { user } = useAuth();
  const { logo, refresh } = useConfig();
  const [preview, setPreview] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  if (user?.rol !== "admin") return <Navigate to="/" replace />;

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
    </div>
  );
}
