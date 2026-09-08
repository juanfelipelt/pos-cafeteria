// Formato de números y monedas con la localización del navegador/SO.

export const MONEDA = "$";

const localeDefault = () =>
  typeof navigator !== "undefined" && navigator.language
    ? navigator.language
    : undefined;

function separators() {
  const sample = new Intl.NumberFormat(localeDefault(), {
    maximumFractionDigits: 2,
  }).formatToParts(1234567.89);
  const dec = sample.find((p) => p.type === "decimal")?.value ?? ".";
  const grp = sample.find((p) => p.type === "group")?.value ?? ",";
  return { dec, grp };
}

export function formatNumber(value: number, maxDecimals = 2): string {
  if (Number.isNaN(value)) return "0";
  return new Intl.NumberFormat(localeDefault(), {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals,
  }).format(value);
}

export function formatMoney(value: number): string {
  return `${MONEDA}${formatNumber(value)}`;
}

export function parseNumber(text: string): number {
  if (!text) return 0;
  const { dec, grp } = separators();
  const normalized = text
    .split(grp)
    .join("")
    .split(dec)
    .join(".")
    .trim();
  const n = parseFloat(normalized);
  return Number.isNaN(n) ? 0 : n;
}

export { separators };
