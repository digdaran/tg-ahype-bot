import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../store/AuthContext";

export default function PrivateRoute() {
  const { user, loading } = useAuth();

  if (loading) return <div className="p-10 text-center text-slate-500">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}
