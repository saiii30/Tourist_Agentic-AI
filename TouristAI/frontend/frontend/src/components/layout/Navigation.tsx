import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Home, MessageSquare, Map, Heart, User, Compass, LogOut } from "lucide-react";
import { motion } from "framer-motion";
import { useTravelPlanner } from "../../context/TravelPlannerContext";

export const Navigation: React.FC = () => {
  const location = useLocation();
  useTravelPlanner();
  const activePath = location.pathname;

  const navItems = [
    { label: "Home", path: "/", icon: Home },
    { label: "AI Chat", path: "/chat", icon: MessageSquare },
    { label: "Trip Planner", path: "/planner", icon: Map },
    { label: "Saved Trips", path: "/saved", icon: Heart },
    { label: "Profile", path: "/profile", icon: User }
  ];

  const isActive = (path: string) => activePath === path;

  return (
    <>
      {/* ── 1. Desktop Left Sidebar (>=1024px) ── */}
      <aside className="hidden lg:flex flex-col w-68 h-screen bg-white dark:bg-[#111827] border-r border-slate-200/80 dark:border-slate-800/80 p-5 sticky top-0 flex-shrink-0 z-20">
        {/* Brand Logo */}
        <div className="flex items-center gap-3 px-2 py-4 mb-6">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-teal-650 bg-teal-600 text-white shadow-md shadow-teal-600/20">
            <Compass className="w-5 h-5 animate-pulse-slow" />
          </div>
          <div>
            <h1 className="font-heading text-lg font-bold tracking-tight text-slate-800 dark:text-slate-100 leading-none">
              Tourist.AI
            </h1>
            <span className="text-[10px] text-teal-600 dark:text-teal-405 font-semibold tracking-wider uppercase">
              Smart Planner
            </span>
          </div>
        </div>

        {/* Links */}
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 group ${
                  active
                    ? "text-teal-600 dark:text-teal-400 bg-teal-50/50 dark:bg-teal-950/20"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-850 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-900"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute left-0 w-1 h-6 bg-teal-600 dark:bg-teal-400 rounded-r-full"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                <Icon className={`w-5 h-5 transition-transform duration-200 group-hover:scale-105 ${
                  active ? "text-teal-600 dark:text-teal-400" : "text-slate-400 dark:text-slate-550"
                }`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer profile card */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="relative">
              <img
                src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
                alt="Avatar"
                className="w-10 h-10 rounded-full object-cover border-2 border-slate-200 dark:border-slate-800 shadow-sm"
              />
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-white dark:border-[#111827] rounded-full" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                Sarah Jenkins
              </p>
              <p className="text-[10px] text-slate-400 truncate">
                sarah.j@google.com
              </p>
            </div>
          </div>
          <button className="flex items-center gap-2.5 w-full px-3 py-2 text-xs font-semibold text-slate-550 dark:text-slate-400 hover:text-red-650 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors">
            <LogOut className="w-4 h-4" />
            Log Out
          </button>
        </div>
      </aside>

      {/* ── 2. Tablet Navigation Rail (640px to 1024px) ── */}
      <aside className="hidden sm:flex lg:hidden flex-col w-20 h-screen bg-white dark:bg-[#111827] border-r border-slate-200 dark:border-slate-805 py-6 px-2 items-center justify-between sticky top-0 flex-shrink-0 z-20">
        
        {/* Compact Logo */}
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-teal-650 bg-teal-600 text-white shadow-sm">
          <Compass className="w-5.5 h-5.5" />
        </div>

        {/* Vertical Rail Icons */}
        <nav className="flex-1 flex flex-col gap-5 pt-8 w-full">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex flex-col items-center gap-1.5 py-2.5 rounded-xl transition-all duration-200 group text-center select-none ${
                  active
                    ? "text-teal-600 dark:text-teal-400 bg-teal-50/50 dark:bg-teal-950/15"
                    : "text-slate-450 dark:text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-900"
                }`}
              >
                <Icon className={`w-5 h-5 transition-transform duration-205 group-hover:scale-105 ${active ? "text-teal-655" : ""}`} />
                <span className="text-[9px] font-bold tracking-wide">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>

        {/* Profile Avatar Trigger */}
        <div className="flex flex-col items-center gap-3">
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
            alt="Profile Avatar"
            className="w-9 h-9 rounded-full object-cover border border-slate-200 dark:border-slate-850 shadow-sm"
          />
        </div>
      </aside>

      {/* ── 3. Mobile Bottom Navigation (<640px) ── */}
      <nav className="fixed bottom-0 left-0 right-0 h-16 bg-white/95 dark:bg-[#111827]/95 backdrop-blur-md border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-around px-2 z-30 sm:hidden">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center flex-1 h-full py-1 text-center select-none ${
                active
                  ? "text-teal-605 text-teal-600 dark:text-teal-400"
                  : "text-slate-455 text-slate-400 dark:text-slate-500"
              }`}
            >
              <div className="relative flex items-center justify-center p-1.5">
                {active && (
                  <motion.span
                    layoutId="mobileNavGlow"
                    className="absolute inset-0 bg-teal-50 dark:bg-teal-950/30 rounded-xl -z-10"
                    transition={{ type: "spring", stiffness: 350, damping: 25 }}
                  />
                )}
                <Icon className={`w-5.5 h-5.5 transition-transform ${active ? "scale-105" : ""}`} />
              </div>
              <span className="text-[10px] font-bold tracking-wide mt-0.5">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </>
  );
};
export default Navigation;
