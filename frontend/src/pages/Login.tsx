import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { useConfig } from "../config";

export default function Login() {
  const { login } = useAuth();
  const { logo } = useConfig();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    }
  }

  return (
    <div className="login">
      <form onSubmit={handleSubmit} className="login-card">
        {logo ? (
          <img className="login-logo" src={logo} alt="Logo" />
        ) : (
          <span className="logo-placeholder large">B</span>
        )}
        <h1>Cafetería POS</h1>
        <p className="muted">Inicia sesión para continuar</p>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="primary">
          Entrar
        </button>
      </form>
    </div>
  );
}
