/*
 * config.tsx — Contexto de configuración global de la aplicación.
 *
 * ¿Qué es? Un contexto de React que guarda ajustes generales de la tienda
 * (por ahora, el logo configurable) y que pueden usarse en cualquier parte.
 *
 * ¿Para qué sirve?
 *   - Cargar una sola vez la configuración desde el backend
 *     (endpoint "/configuracion").
 *   - Exponer el logo actual y una función refresh() para volver a cargarla
 *     cuando el usuario lo cambie desde la página de Configuración.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   App.tsx envuelve todo con <ConfigProvider>. El Layout y las páginas
 *   usan el hook useConfig() para mostrar el logo, etc.
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

// Contrato del valor que comparte el contexto de configuración.
interface ConfigValue {
  logo: string | null; // Logo actual (data URL o URL), o null si no hay.
  refresh: () => Promise<void>; // Volver a cargar la configuración.
}

// Contexto con valores por defecto, para que exista siempre un valor válido
// incluso antes de que el provider cargue los datos reales.
const ConfigContext = createContext<ConfigValue>({
  logo: null,
  refresh: async () => {},
});

// Provider: carga la configuración y la comparte con toda la app.
export function ConfigProvider({ children }: { children: ReactNode }) {
  // Estado con el logo. Arranca en null (aún no cargado).
  const [logo, setLogo] = useState<string | null>(null);

  // refresh: pide la configuración al backend y guarda el logo.
  async function refresh() {
    try {
      const data = await api<Record<string, string>>("/configuracion");
      // Usamos ?? null: si data.logo no existe, guardamos null.
      setLogo(data.logo ?? null);
    } catch {
      /* el logo es opcional */
      // Si falla la petición no rompemos la app: el logo simplemente queda null.
    }
  }

  // Al montar el provider, cargamos la configuración una vez.
  useEffect(() => {
    refresh();
  }, []);

  // Compartimos el logo y la función refresh con los componentes hijos.
  return (
    <ConfigContext.Provider value={{ logo, refresh }}>
      {children}
    </ConfigContext.Provider>
  );
}

// Hook para leer (y refrescar) la configuración desde cualquier componente.
export function useConfig(): ConfigValue {
  return useContext(ConfigContext);
}
