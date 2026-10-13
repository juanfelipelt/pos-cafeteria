/*
 * lib/format.ts — Utilidades para dar formato a números y monedas.
 *
 * ¿Qué es? Un pequeño módulo de funciones auxiliares (helpers) que se encargan
 * de mostrar y leer números según la configuración regional del navegador
 * (por ejemplo, en español se usa "." para miles y "," para decimales).
 *
 * ¿Para qué sirve?
 *   - formatNumber: convierte un número en texto bonito (1.234,56).
 *   - formatMoney: agrega el símbolo de moneda ($).
 *   - parseNumber: hace lo contrario, convierte el texto escrito por el
 *     usuario en un número real.
 *   - separators: detecta qué símbolo usa el locale para decimales y miles.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   Lo usan el componente MoneyInput y las páginas para mostrar precios y
 *   totales, y para interpretar los valores que el usuario escribe.
 */

// Formato de números y monedas con la localización del navegador/SO.

// Símbolo de moneda que se antepone a los montos.
export const MONEDA = "$";

// Devuelve el idioma configurado en el navegador (p. ej. "es-CO").
// Si no está disponible, devuelve undefined para que Intl use el del sistema.
const localeDefault = () =>
  typeof navigator !== "undefined" && navigator.language
    ? navigator.language
    : undefined;

// separators: averigua qué caracteres usa el locale actual para separar
// decimales y grupos de miles. Se apoya en Intl.NumberFormat, que formatea
// el número 1234567.89 y nos dice con qué símbolos lo hace.
function separators() {
  const sample = new Intl.NumberFormat(localeDefault(), {
    maximumFractionDigits: 2,
  }).formatToParts(1234567.89);
  // Buscamos las partes que representan el separador decimal y el de grupos.
  const dec = sample.find((p) => p.type === "decimal")?.value ?? ".";
  const grp = sample.find((p) => p.type === "group")?.value ?? ",";
  return { dec, grp };
}

// formatNumber: da formato a un número con separadores de miles y un máximo
// de decimales indicado (por defecto 2).
export function formatNumber(value: number, maxDecimals = 2): string {
  if (Number.isNaN(value)) return "0"; // Protección ante valores inválidos.
  return new Intl.NumberFormat(localeDefault(), {
    minimumFractionDigits: 0, // Sin decimales obligatorios.
    maximumFractionDigits: maxDecimals, // Hasta maxDecimals decimales.
  }).format(value);
}

// formatMoney: igual que formatNumber pero anteponiendo el símbolo de moneda.
export function formatMoney(value: number): string {
  return `${MONEDA}${formatNumber(value)}`;
}

// parseNumber: convierte el texto que escribe el usuario en un número.
// Ejemplo: "1.234,56" -> 1234.56 (limpiando separadores de miles y
// cambiando la coma decimal por un punto).
export function parseNumber(text: string): number {
  if (!text) return 0; // Texto vacío = cero.
  const { dec, grp } = separators();
  const normalized = text
    .split(grp) // Quitamos los separadores de miles.
    .join("")
    .split(dec) // Cambiamos el separador decimal por ".".
    .join(".")
    .trim();
  const n = parseFloat(normalized);
  return Number.isNaN(n) ? 0 : n; // Si no es un número, devolvemos 0.
}

// Reexportamos separators para que otros módulos puedan conocer los símbolos.
export { separators };
