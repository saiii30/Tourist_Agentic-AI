import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { Compass, Eye, EyeOff, LogIn, UserPlus } from "lucide-react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

const fieldClass = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950";

export default function Auth() {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const requestedDestination = (location.state as { from?: string } | null)?.from;
  const destination = requestedDestination?.startsWith("/") && requestedDestination !== "/auth"
    ? requestedDestination
    : "/";

  if (user) return <Navigate to={destination} replace />;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, displayName);
      navigate(destination, { replace: true });
    } catch (reason) {
      const message = axios.isAxiosError(reason) ? reason.response?.data?.detail : null;
      setError(typeof message === "string" ? message : "Unable to authenticate. Check the server and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-5xl place-items-center px-4 py-10">
      <div className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-[#111827] md:grid-cols-2">
        <section className="hidden bg-gradient-to-br from-teal-600 to-cyan-800 p-10 text-white md:flex md:flex-col md:justify-between">
          <Compass className="h-10 w-10" />
          <div><h1 className="text-3xl font-extrabold">Your journeys, remembered.</h1><p className="mt-3 text-sm text-teal-50">Sign in to keep travel preferences and saved plans tied securely to your account.</p></div>
          <p className="text-xs text-teal-100">Guest planning and AI chat remain available without an account.</p>
        </section>
        <form onSubmit={submit} className="space-y-5 p-7 sm:p-10">
          <div><h2 className="text-2xl font-extrabold text-slate-800 dark:text-white">{mode === "login" ? "Welcome back" : "Create account"}</h2><p className="mt-1 text-xs text-slate-500">{mode === "login" ? "Sign in to access your profile and saved trips." : "Use at least 10 characters with a letter and number."}</p></div>
          {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-semibold text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">{error}</div>}
          {mode === "register" && <label className="block text-xs font-bold text-slate-600 dark:text-slate-300">Display name<input required minLength={2} autoComplete="name" className={`${fieldClass} mt-1.5`} value={displayName} onChange={e => setDisplayName(e.target.value)} /></label>}
          <label className="block text-xs font-bold text-slate-600 dark:text-slate-300">Email<input required type="email" autoComplete="email" className={`${fieldClass} mt-1.5`} value={email} onChange={e => setEmail(e.target.value)} /></label>
          <label className="block text-xs font-bold text-slate-600 dark:text-slate-300">Password<div className="relative mt-1.5"><input required minLength={10} type={showPassword ? "text" : "password"} autoComplete={mode === "login" ? "current-password" : "new-password"} className={`${fieldClass} pr-12`} value={password} onChange={e => setPassword(e.target.value)} /><button type="button" onClick={() => setShowPassword(v => !v)} className="absolute right-3 top-3 text-slate-400" aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}</button></div></label>
          <button disabled={submitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 px-4 py-3 text-sm font-bold text-white hover:bg-teal-700 disabled:opacity-60">{mode === "login" ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}{submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
          <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }} className="w-full text-xs font-semibold text-teal-700 dark:text-teal-400">{mode === "login" ? "New traveler? Create an account" : "Already registered? Sign in"}</button>
        </form>
      </div>
    </div>
  );
}
