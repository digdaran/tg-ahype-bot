import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../store/AuthContext";
import { apiErrorMessage } from "../api/client";

export default function LoginPage() {
  const { user, login } = useAuth();
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(loginValue, password);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <form onSubmit={handleSubmit} className="card w-full max-w-sm">
        <h1 className="text-xl font-bold mb-1">🎟 Raffle Admin</h1>
        <p className="text-sm text-slate-500 mb-6">Вход в панель администратора</p>

        {error && <div className="mb-4 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</div>}

        <label className="block text-sm font-medium mb-1">Логин</label>
        <input className="input mb-4" value={loginValue} onChange={(e) => setLoginValue(e.target.value)} required />

        <label className="block text-sm font-medium mb-1">Пароль</label>
        <input
          className="input mb-6"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" className="btn-primary w-full" disabled={submitting}>
          {submitting ? "Вход…" : "Войти"}
        </button>
      </form>
    </div>
  );
}
