const MAX_DEFECTO = 600;
const CALIDAD_DEFECTO = 0.72;

function leerComoDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () =>
      reject(reader.error ?? new Error("No se pudo leer el archivo"));
    reader.readAsDataURL(file);
  });
}

function cargarImagen(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Imagen inválida"));
    img.src = src;
  });
}

export interface OpcionesImagen {
  /** Lado máximo (ancho/alto) en px. Por defecto 600. */
  maxSize?: number;
  /** Calidad 0..1 para JPEG. Por defecto 0.72. */
  quality?: number;
  /** Tipo de salida. Por defecto: PNG si el origen es PNG (conserva transparencia), si no JPEG. */
  type?: "image/jpeg" | "image/png";
}

/**
 * Lee una imagen y la devuelve como data URL comprimida (redimensionada y
 * recomprimida) para guardarla sin inflar la base de datos.
 */
export async function comprimirImagen(
  file: File,
  opciones: OpcionesImagen = {}
): Promise<string> {
  const {
    maxSize = MAX_DEFECTO,
    quality = CALIDAD_DEFECTO,
    type = file.type === "image/png" ? "image/png" : "image/jpeg",
  } = opciones;

  // Los SVG no se rasterizan bien y ya son livianos: se guardan tal cual.
  if (file.type === "image/svg+xml") return leerComoDataUrl(file);

  const original = await leerComoDataUrl(file);
  const img = await cargarImagen(original);

  const escala = Math.min(1, maxSize / Math.max(img.width, img.height));
  const ancho = Math.max(1, Math.round(img.width * escala));
  const alto = Math.max(1, Math.round(img.height * escala));

  const canvas = document.createElement("canvas");
  canvas.width = ancho;
  canvas.height = alto;
  const ctx = canvas.getContext("2d");
  if (!ctx) return original;

  if (type === "image/jpeg") {
    // JPEG no soporta transparencia: fondo blanco para que no salga negro.
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, ancho, alto);
  }
  ctx.drawImage(img, 0, 0, ancho, alto);

  const salida = canvas.toDataURL(type, quality);
  // Si recomprimir no reduce el tamaño, conserva el original.
  return salida.length < original.length ? salida : original;
}
