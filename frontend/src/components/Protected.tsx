import { Navigate } from "react-router-dom";
import { useAuth } from "../auth";
import type { ReactNode } from "react";

export default function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="loading-screen">Cargando…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
