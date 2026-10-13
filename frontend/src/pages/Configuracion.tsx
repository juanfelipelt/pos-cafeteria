/*
 * ============================================================================
 * PÁGINA: Configuración
 * ============================================================================
 * ¿Qué es este archivo?
 *   Es la pantalla de ajustes generales del negocio. Desde aquí el
 *   administrador puede:
 *     1) Subir/cambiar el LOGO que aparece en el menú y en el login.
 *     2) Elegir los DÍAS LABORABLES de la semana (para repartir los costos
 *        fijos mensuales entre los días que realmente se trabaja).
 *
 * ¿Para qué sirve?
 *   Personaliza la aplicación con la marca del negocio y da la base para
 *   los cálculos diarios de la pantalla Costeo (punto de equilibrio).
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   - Usa `api` (../api) para leer y guardar la configuración en el backend
 *     (/configuracion, /configuracion/logo, /configuracion/dias_laborales).
 *   - Usa `useConfig` (../config) para obtener el logo actual y refrescarlo
 *     tras guardarlo (así se actualiza en toda la app).
 *   - Usa `comprimirImagen` (../lib/image) para reducir la imagen del logo
 *     antes de subirla y no gastar espacio de más.
 *   - Usa `useAuth` (../auth) para permitir el acceso solo a administradores.
 * ============================================================================
 */

import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useConfig } from "../config";
import { comprimirImagen } from "../lib/image";

// Días de la semana: `n` es el número 1..7 (lunes..domingo) y `label` la
// abreviatura que se muestra en los botones.
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
  // `logo` es el logo actual (global) y `refresh` lo vuelve a cargar.
  const { logo, refresh } = useConfig();

  // ------------------------------ ESTADO ---------------------------------
  // Vista previa del logo que el usuario acaba de elegir (aún sin guardar).
  const [preview, setPreview] = useState<string | null>(null);
  // Mensajes de éxito y de error del bloque de logo.
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  // Referencia al <input type="file"> para poder abrirlo/limpiarlo por código.
  const fileRef = useRef<HTMLInputElement>(null);

  // Días laborables seleccionados (por defecto lunes a sábado). Y su mensaje.
  const [dias, setDias] = useState<number[]>([1, 2, 3, 4, 5, 6]);
  const [mensajeDias, setMensajeDias] = useState("");

  // EFECTO: al montar, lee los días laborables guardados y los pone en el
  // estado. El backend los guarda como texto "1,2,3,...", así que los
  // convertimos a números y descartamos valores fuera de rango 1..7.
  useEffect(() => {
    api<Record<string, string>>("/configuracion")
      .then((data) => {
        if (data.dias_laborales) {
          const nums = data.dias_laborales
            .split(",")
            .map((x) => Number(x.trim()))
            .filter((n) => n >= 1 && n <= 7);
          // Solo actualizamos si quedó al menos un día válido.
          if (nums.length) setDias(nums);
        }
      })
      // Si falla, lo ignoramos silenciosamente (dejamos los valores por defecto).
      .catch(() => {});
  }, []);

  // GUARDA DE SEGURIDAD: solo administradores; el resto va al inicio.
  if (user?.rol !== "admin") return <Navigate to="/" replace />;

  // Activa o desactiva un día laborable. Si ya estaba, lo quita; si no,
  // lo agrega y deja el arreglo ordenado de menor a mayor.
  function toggleDia(n: number) {
    setDias((prev) =>
      prev.includes(n) ? prev.filter((d) => d !== n) : [...prev, n].sort()
    );
    setMensajeDias(""); // Ocultamos el mensaje anterior al haber un cambio.
  }

  // Guarda los días laborables elegidos en el backend.
  async function guardarDias() {
    setError("");
    setMensajeDias("");
    try {
      await api("/configuracion/dias_laborales", {
        method: "PUT",
        body: JSON.stringify({ valor: dias.join(",") }), // Ej: "1,2,3,4,5,6".
      });
      setMensajeDias("Días laborables actualizados.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  }

  // Se ejecuta cuando el usuario elige un archivo de imagen. Comprime la
  // imagen (para que pese menos) y guarda el resultado como vista previa.
  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]; // Primer archivo seleccionado.
    if (!file) return;
    try {
      setPreview(await comprimirImagen(file, { maxSize: 400 }));
    } catch {
      setError("No se pudo procesar la imagen.");
    }
  }

  // Guarda el nuevo logo en el backend y refresca el logo global.
  async function guardar() {
    if (!preview) return; // Nada que guardar si no hay vista previa.
    setError("");
    setMensaje("");
    try {
      await api("/configuracion/logo", {
        method: "PUT",
        body: JSON.stringify({ logo: preview }),
      });
      await refresh(); // Recarga el logo para que cambie en toda la app.
      setPreview(null); // Quitamos la vista previa (ya quedó guardado).
      setMensaje("Logo actualizado correctamente.");
      // Limpiamos el input de archivo para poder elegir el mismo otra vez.
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  }

  return (
    <div>
      <h2>Configuración</h2>

      {/* Sección 1: gestión del logo del negocio. */}
      <section className="card">
        <h3>Logo</h3>
        <p className="muted">
          Este logo aparece en el menú lateral y en la pantalla de inicio de
          sesión.
        </p>

        <div className="logo-editor">
          {/* Vista previa: primero la recién elegida; si no, el logo actual;
              y si tampoco hay, un texto de marcador. */}
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
            {/* Input de archivo oculto, controlado mediante fileRef. */}
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={onFile}
              hidden
            />
            {/* Abre el selector de archivos del sistema. */}
            <button type="button" onClick={() => fileRef.current?.click()}>
              Elegir imagen
            </button>
            {/* Guardar se desactiva mientras no haya una imagen elegida. */}
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

        {/* Mensajes de resultado del guardado del logo. */}
        {mensaje && <p className="ok">{mensaje}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      {/* Sección 2: selección de días laborables. */}
      <section className="card">
        <h3>Días laborables</h3>
        <p className="muted">
          Se usan para repartir los costos fijos mensuales entre los días que
          trabajas (punto de equilibrio y utilidad diaria).
        </p>
        {/* Botones tipo "chip": se pintan activos según `dias`. */}
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
        {/* Mensaje de éxito al guardar los días. */}
        {mensajeDias && <p className="ok">{mensajeDias}</p>}
      </section>
    </div>
  );
}
