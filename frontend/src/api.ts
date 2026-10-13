/*
 * api.ts — Capa de comunicación con el backend (API REST).
 *
 * ¿Qué es? El "puente" entre el front-end y el servidor. Agrupa en un solo
 * lugar cómo se hacen las peticiones HTTP, cómo se guarda el token de sesión
 * y cómo se manejan los errores.
 *
 * ¿Para qué sirve?
 *   - getToken/setToken/clearToken: leer, guardar y borrar el token JWT del
 *     localStorage del navegador.
 *   - ApiError: clase de error propia que incluye el código de estado HTTP.
 *   - api<T>() : función genérica que hace peticiones (GET, POST, etc.),
 *     agrega el token y el Content-Type automáticamente, y traduce los
 *     errores del backend a mensajes legibles.
 *   - eventSourceUrl: construye la URL completa para flujos en tiempo real
 *     (Server-Sent Events).
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   auth.tsx usa api() para login y para obtener el usuario. Prácticamente
 *   todas las páginas (Productos, Ventas, etc.) obtienen sus datos llamando
 *   a api(). BASE apunta al servidor backend.
 */

// Dirección base del backend. Se toma de la variable de entorno VITE_API_URL;
// si no está definida, por defecto se usa el servidor local de desarrollo.
const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// preconnectApi: pista de rendimiento. Le dice al navegador que empiece a
// abrir la conexión con el servidor desde el inicio, para que las primeras
// peticiones sean un poco más rápidas.
function preconnectApi(): void {
  try {
    const origin = new URL(BASE).origin; // Solo el dominio (sin la ruta).
    if (!origin || typeof document === "undefined") return;
    const link = document.createElement("link");
    link.rel = "preconnect"; // Tipo de pista: pre-conectar.
    link.href = origin;
    link.crossOrigin = "anonymous";
    document.head.appendChild(link); // Insertamos la etiqueta en el <head>.
  } catch {
    /* URL inválida: se ignora */
    // Si BASE no es una URL válida, simplemente no hacemos la optimización.
  }
}
preconnectApi(); // Se ejecuta al cargar el módulo.

// getToken: lee el token de sesión guardado en el navegador.
export function getToken(): string | null {
  return localStorage.getItem("token");
}

// setToken: guarda el token en el navegador tras iniciar sesión.
export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

// clearToken: elimina el token (al cerrar sesión o si expira).
export function clearToken(): void {
  localStorage.removeItem("token");
}

// Clase de error personalizada que conserva el código de estado HTTP (401,
// 404, 500...), útil para saber qué salió mal.
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message); // Llama al constructor de Error con el mensaje.
    this.status = status;
  }
}

// api<T>: función central que hace las peticiones al backend.
// El <T> es el tipo de dato que esperamos recibir (por ejemplo User[]).
export async function api<T = unknown>(
  path: string, // Ruta del endpoint, por ejemplo "/productos".
  options: RequestInit = {} // Opciones extra (método, body, etc.).
): Promise<T> {
  const token = getToken();
  // Copiamos las cabeceras que nos hayan pasado para no modificarlas.
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  // Si enviamos datos, avisamos que el cuerpo es JSON.
  if (options.body) headers["Content-Type"] = "application/json";
  // Si hay token, lo adjuntamos como Bearer para autenticarnos.
  if (token) headers["Authorization"] = `Bearer ${token}`;

  // Ejecutamos la petición real al servidor con la URL completa.
  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  // Si el servidor responde 401 (no autorizado) y NO es el propio login,
  // significa que la sesión expiró: borramos el token y mandamos al login.
  if (res.status === 401 && !path.startsWith("/auth/login")) {
    clearToken();
    window.location.href = "/login";
    throw new ApiError("No autenticado", 401);
  }

  // Si la respuesta no fue exitosa (por ejemplo 400 o 500), intentamos leer
  // el detalle del error que envía el backend para mostrar un mensaje claro.
  if (!res.ok) {
    let detail = res.statusText; // Mensaje por defecto.
    try {
      const data = await res.json();
      if (typeof data.detail === "string") {
        // Caso simple: el backend manda un texto en "detail".
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        // Caso típico de validación (FastAPI): lista de errores con "msg"
        // y "loc". Los unimos en una sola frase legible.
        detail = data.detail
          .map((d: { msg?: string; loc?: unknown[] }) =>
            typeof d?.msg === "string"
              ? `${(d.loc?.slice(1) || []).join(".")}: ${d.msg}`
              : String(d)
          )
          .filter(Boolean) // Quitamos elementos vacíos.
          .join(" · "); // Separamos con un punto medio.
      } else if (data.detail) {
        // Cualquier otro tipo de detalle: lo mostramos como texto JSON.
        detail = JSON.stringify(data.detail);
      }
    } catch {
      /* noop */
      // Si el cuerpo no era JSON, conservamos el mensaje por defecto.
    }
    throw new ApiError(detail, res.status); // Lanzamos el error ya traducido.
  }

  // Éxito: convertimos la respuesta JSON al tipo T esperado y la devolvemos.
  return res.json() as Promise<T>;
}

// eventSourceUrl: arma la URL completa para conexiones en tiempo real
// (EventSource / Server-Sent Events), que no usan fetch ni cabeceras.
export function eventSourceUrl(path: string): string {
  return `${BASE}${path}`;
}
