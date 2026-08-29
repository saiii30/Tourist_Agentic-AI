import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="grid min-h-[60vh] place-items-center text-sm text-slate-500">Checking your session…</div>;
  if (!user) return <Navigate to="/auth" replace state={{ from: location.pathname }} />;
  return children;
}
