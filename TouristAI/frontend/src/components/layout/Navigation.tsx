import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Bot, Map, ListChecks, Heart, User, Compass, LogOut, Train, Plane, Bus, TicketCheck, ChevronDown, PanelLeftClose, PanelLeftOpen, Languages } from "lucide-react";
import { motion } from "framer-motion";
import { useTravelPlanner } from "../../context/TravelPlannerContext";
import { useAuth } from "../../context/AuthContext";

export const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  useTravelPlanner();
  const activePath = location.pathname;
  const [isExpanded, setIsExpanded] = useState(() => localStorage.getItem("tourist-sidebar-expanded") !== "false");
  const [ticketsOpen, setTicketsOpen] = useState(() => ["/trains", "/flights", "/buses"].some((path) => activePath.startsWith(path)));

  const toggleSidebar = () => {
    setIsExpanded((current) => {
      const next = !current;
      localStorage.setItem("tourist-sidebar-expanded", String(next));
      return next;
    });
  };

  const ticketItems = [
    { label: "Train Tickets", path: "/trains", icon: Train },
    { label: "Bus Tickets", path: "/buses", icon: Bus },
    { label: "Flight Tickets", path: "/flights", icon: Plane },
  ];

  const navItems = [
    { label: "AI Home", path: "/", icon: Bot },
    { label: "Trip Planner", path: "/planner", icon: Map },
    { label: "Itinerary", path: "/itinerary", icon: ListChecks },
    { label: "Tickets", path: "/tickets", icon: TicketCheck, children: ticketItems },
    { label: "Saved Trips", path: "/saved", icon: Heart },
    { label: "Local Assist", path: "/local-assist", icon: Languages },
    { label: "Profile", path: "/profile", icon: User }
  ];

  const mobileNavItems = navItems.filter((item) =>
    ["/", "/planner", "/itinerary", "/local-assist", "/saved", "/profile"].includes(item.path)
  );

  const isActive = (path: string) => activePath === path || (path !== "/" && activePath.startsWith(`${path}/`));
  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      navigate("/auth", { replace: true });
    }
  };

  return (
    <>
      {/* ── 1. Desktop Left Sidebar (>=1024px) ── */}
      <aside className={`hidden lg:flex flex-col h-screen bg-white dark:bg-[#111827] border-r border-slate-200/80 dark:border-slate-800/80 sticky top-0 flex-shrink-0 z-20 transition-[width,padding] duration-300 ${isExpanded ? "w-68 p-5" : "w-20 px-2 py-5"}`}>
        {/* Brand Logo */}
        <div className={`flex items-center py-4 mb-5 ${isExpanded ? "gap-3 px-2" : "justify-center"}`}>
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-teal-650 bg-teal-600 text-white shadow-md shadow-teal-600/20">
            <Compass className="w-5 h-5 animate-pulse-slow" />
          </div>
          {isExpanded && <div>
            <h1 className="font-heading text-lg font-bold tracking-tight text-slate-800 dark:text-slate-100 leading-none">
              Tourist.AI
            </h1>
            <span className="text-[10px] text-teal-600 dark:text-teal-405 font-semibold tracking-wider uppercase">
              Smart Planner
            </span>
          </div>}
        </div>

        <button
          onClick={toggleSidebar}
          className={`mb-4 flex min-h-9 items-center rounded-xl border border-slate-200/70 text-slate-500 transition-colors hover:border-teal-200 hover:bg-teal-50 hover:text-teal-700 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-teal-950/20 dark:hover:text-teal-400 ${isExpanded ? "justify-between px-3" : "justify-center px-2"}`}
          title={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
          aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isExpanded && <span className="text-[10px] font-extrabold uppercase tracking-wide">Menu</span>}
          {isExpanded ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
        </button>

        {/* Links */}
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = item.children ? item.children.some((child) => isActive(child.path)) : isActive(item.path);
            if (item.children) {
              return (
                <div key={item.path} className="space-y-1">
                  <button
                    type="button"
                    onClick={() => {
                      if (!isExpanded) {
                        setIsExpanded(true);
                        localStorage.setItem("tourist-sidebar-expanded", "true");
                        setTicketsOpen(true);
                        return;
                      }
                      setTicketsOpen((open) => !open);
                    }}
                    title={!isExpanded ? item.label : undefined}
                    aria-expanded={ticketsOpen}
                    className={`relative flex w-full items-center rounded-xl text-sm font-semibold transition-all duration-200 group ${isExpanded ? "gap-3 px-4 py-3" : "justify-center px-2 py-3"} ${active ? "bg-teal-50/50 text-teal-600 dark:bg-teal-950/20 dark:text-teal-400" : "text-slate-500 hover:bg-slate-50 hover:text-slate-850 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-200"}`}
                  >
                    {active && <span className="absolute left-0 h-6 w-1 rounded-r-full bg-teal-600 dark:bg-teal-400" />}
                    <Icon className={`h-5 w-5 ${active ? "text-teal-600 dark:text-teal-400" : "text-slate-400"}`} />
                    {isExpanded && <><span className="flex-1 text-left">Tickets</span><ChevronDown className={`h-4 w-4 transition-transform ${ticketsOpen ? "rotate-180" : ""}`} /></>}
                  </button>
                  {isExpanded && ticketsOpen && (
                    <div className="ml-5 space-y-1 border-l border-slate-200 pl-3 dark:border-slate-800">
                      {item.children.map((child) => {
                        const ChildIcon = child.icon;
                        const childActive = isActive(child.path);
                        return <Link key={child.path} to={child.path} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-bold ${childActive ? "bg-teal-50 text-teal-700 dark:bg-teal-950/25 dark:text-teal-300" : "text-slate-500 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-900"}`}><ChildIcon className="h-4 w-4" />{child.label}</Link>;
                      })}
                    </div>
                  )}
                </div>
              );
            }
            return (
              <Link
                key={item.path}
                to={item.path}
                title={!isExpanded ? item.label : undefined}
                aria-label={item.label}
                className={`relative flex items-center rounded-xl text-sm font-semibold transition-all duration-200 group ${isExpanded ? "gap-3 px-4 py-3" : "justify-center px-2 py-3"} ${active
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
                <Icon className={`w-5 h-5 transition-transform duration-200 group-hover:scale-105 ${active ? "text-teal-600 dark:text-teal-400" : "text-slate-400 dark:text-slate-550"
                  }`} />
                {isExpanded && item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer profile card */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className={`flex items-center py-1 ${isExpanded ? "gap-3 px-2" : "justify-center"}`}>
            <div className="relative">
              <img
                src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
                alt="Avatar"
                className="w-10 h-10 rounded-full object-cover border-2 border-slate-200 dark:border-slate-800 shadow-sm"
              />
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-white dark:border-[#111827] rounded-full" />
            </div>
            {isExpanded && <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                {user?.display_name || "Guest Traveler"}
              </p>
              <p className="text-[10px] text-slate-400 truncate">
                {user?.email || "Sign in to save trips"}
              </p>
            </div>}
          </div>
          {user ? (
            <button type="button" onClick={handleLogout} title="Log Out" aria-label="Log Out" className={`flex items-center w-full py-2 text-xs font-semibold text-slate-550 dark:text-slate-400 hover:text-red-650 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors ${isExpanded ? "gap-2.5 px-3" : "justify-center px-2"}`}>
              <LogOut className="w-4 h-4" />
              {isExpanded && "Log Out"}
            </button>
          ) : (
            <Link to="/auth" className={`flex items-center w-full py-2 text-xs font-semibold text-teal-700 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-950/20 rounded-lg transition-colors ${isExpanded ? "gap-2.5 px-3" : "justify-center px-2"}`}>
              <LogOut className="w-4 h-4 rotate-180" />
              {isExpanded && "Sign In"}
            </Link>
          )}
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
            const active = item.children ? item.children.some((child) => isActive(child.path)) : isActive(item.path);
            if (item.children) {
              return (
                <div key={item.path} className="relative">
                  <button type="button" onClick={() => setTicketsOpen((open) => !open)} className={`relative flex w-full flex-col items-center gap-1.5 rounded-xl py-2.5 text-center transition-all ${active ? "bg-teal-50/50 text-teal-600 dark:bg-teal-950/15 dark:text-teal-400" : "text-slate-450 hover:bg-slate-50 dark:text-slate-500 dark:hover:bg-slate-900"}`}>
                    <Icon className="h-5 w-5" /><span className="text-[9px] font-bold">Tickets</span>
                  </button>
                  {ticketsOpen && (
                    <div className="absolute left-16 top-0 z-50 w-44 space-y-1 rounded-xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-800 dark:bg-[#111827]">
                      {item.children.map((child) => { const ChildIcon = child.icon; return <Link key={child.path} to={child.path} className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-bold text-slate-600 hover:bg-teal-50 hover:text-teal-700 dark:text-slate-300 dark:hover:bg-teal-950/25"><ChildIcon className="h-4 w-4" />{child.label}</Link>; })}
                    </div>
                  )}
                </div>
              );
            }
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex flex-col items-center gap-1.5 py-2.5 rounded-xl transition-all duration-200 group text-center select-none ${active
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
        {mobileNavItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center flex-1 h-full py-1 text-center select-none ${active
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
