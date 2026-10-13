/*
 * lib/image.ts — Utilidades para procesar imágenes antes de subirlas.
 *
 * ¿Qué es? Un módulo que toma una imagen elegida por el usuario (un File) y
 * la transforma en una versión comprimida y redimensionada (data URL), lista
 * para guardar sin llenar la base de datos con archivos enormes.
 *
 * ¿Para qué sirve?
 *   - Leer el archivo y convertirlo a data URL.
 *   - Cargarlo como imagen para conocer su tamaño real.
 *   - Dibujarlo en un <canvas> más pequeño y recomprimirlo (JPEG/PNG).
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   Lo usan las páginas que permiten subir fotos (productos, logo de la
 *   tienda, etc.) para no guardar imágenes demasiado grandes.
 */

// Valores por defecto: lado máximo de 600 px y calidad JPEG de 0.72 (0..1).
const MAX_DEFECTO = 600;
const CALIDAD_DEFECTO = 0.72;

// leerComoDataUrl: lee un archivo del disco y lo devuelve como texto
// "data URL" (una cadena base64 que representa el contenido del archivo).
// Se envuelve en una Promise porque FileReader trabaja con eventos.
function leerComoDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string); // Éxito.
    reader.onerror = () =>
      reject(reader.error ?? new Error("No se pudo leer el archivo")); // Error.
    reader.readAsDataURL(file); // Inicia la lectura.
  });
}

// cargarImagen: crea un objeto Image a partir de un src (data URL) y espera
// a que el navegador la haya cargado para poder medirla y dibujarla.
function cargarImagen(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img); // La imagen cargó correctamente.
    img.onerror = () => reject(new Error("Imagen inválida")); // Falló.
    img.src = src;
  });
}

// Opciones de compresión configurables por quien llame a comprimirImagen.
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
  // Desestructuramos las opciones aplicando los valores por defecto.
  const {
    maxSize = MAX_DEFECTO,
    quality = CALIDAD_DEFECTO,
    // Si el origen es PNG mantenemos PNG (para conservar transparencia);
    // en cualquier otro caso salimos como JPEG.
    type = file.type === "image/png" ? "image/png" : "image/jpeg",
  } = opciones;

  // Los SVG no se rasterizan bien y ya son livianos: se guardan tal cual.
  if (file.type === "image/svg+xml") return leerComoDataUrl(file);

  // Leemos el archivo original y lo cargamos como imagen para medirlo.
  const original = await leerComoDataUrl(file);
  const img = await cargarImagen(original);

  // Calculamos la escala para que el lado más grande no supere maxSize.
  // Math.min(1, ...) evita AMPLIAR imágenes que ya son pequeñas.
  const escala = Math.min(1, maxSize / Math.max(img.width, img.height));
  const ancho = Math.max(1, Math.round(img.width * escala));
  const alto = Math.max(1, Math.round(img.height * escala));

  // Creamos un lienzo (canvas) del tamaño calculado y obtenemos su contexto 2D.
  const canvas = document.createElement("canvas");
  canvas.width = ancho;
  canvas.height = alto;
  const ctx = canvas.getContext("2d");
  if (!ctx) return original; // Si el navegador no soporta canvas, no comprime.

  if (type === "image/jpeg") {
    // JPEG no soporta transparencia: fondo blanco para que no salga negro.
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, ancho, alto);
  }
  // Dibujamos la imagen original ya redimensionada dentro del canvas.
  ctx.drawImage(img, 0, 0, ancho, alto);

  // Convertimos el canvas a data URL con el tipo y la calidad deseados.
  const salida = canvas.toDataURL(type, quality);
  // Si recomprimir no reduce el tamaño, conserva el original.
  return salida.length < original.length ? salida : original;
}
