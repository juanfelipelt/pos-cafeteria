export const MONEDA = "$";

export function formatNumber(value: number, maxDecimals = 2): string {
  if (Number.isNaN(value)) return "0";
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals,
  }).format(value);
}

export function formatMoney(value: number): string {
  return `${MONEDA}${formatNumber(value)}`;
}

export function parseNumber(text: string): number {
  if (!text) return 0;
  const normalized = text.replace(/\./g, "").replace(",", ".");
  const n = parseFloat(normalized);
  return Number.isNaN(n) ? 0 : n;
}
