const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function preconnectApi(): void {
  try {
    const origin = new URL(BASE).origin;
    if (!origin || typeof document === "undefined") return;
    const link = document.createElement("link");
    link.rel = "preconnect";
    link.href = origin;
    link.crossOrigin = "anonymous";
    document.head.appendChild(link);
  } catch {
    /* URL inválida: se ignora */
  }
}
preconnectApi();

export function getToken(): string | null {
  return localStorage.getItem("token");
}

export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

export function clearToken(): void {
  localStorage.removeItem("token");
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (options.body) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401 && !path.startsWith("/auth/login")) {
    clearToken();
    window.location.href = "/login";
    throw new ApiError("No autenticado", 401);
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        detail = data.detail
          .map((d: { msg?: string; loc?: unknown[] }) =>
            typeof d?.msg === "string"
              ? `${(d.loc?.slice(1) || []).join(".")}: ${d.msg}`
              : String(d)
          )
          .filter(Boolean)
          .join(" · ");
      } else if (data.detail) {
        detail = JSON.stringify(data.detail);
      }
    } catch {
      /* noop */
    }
    throw new ApiError(detail, res.status);
  }

  return res.json() as Promise<T>;
}

export function eventSourceUrl(path: string): string {
  return `${BASE}${path}`;
}
