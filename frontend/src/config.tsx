import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

interface ConfigValue {
  logo: string | null;
  refresh: () => Promise<void>;
}

const ConfigContext = createContext<ConfigValue>({
  logo: null,
  refresh: async () => {},
});

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [logo, setLogo] = useState<string | null>(null);

  async function refresh() {
    try {
      const data = await api<Record<string, string>>("/configuracion");
      setLogo(data.logo ?? null);
    } catch {
      /* el logo es opcional */
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <ConfigContext.Provider value={{ logo, refresh }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig(): ConfigValue {
  return useContext(ConfigContext);
}
