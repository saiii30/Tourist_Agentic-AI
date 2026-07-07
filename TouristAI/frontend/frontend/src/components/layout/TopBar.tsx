import React from "react";
import { useLocation } from "react-router-dom";
import { Menu, Sun, Moon, Sparkles, Wifi } from "lucide-react";
import { useTravelPlanner } from "../../context/TravelPlannerContext";

interface TopBarProps {
  onMenuClick: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onMenuClick }) => {
  const { theme, toggleTheme } = useTravelPlanner();
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/":
        return "Travel Discoveries";
      case "/chat":
        return "AI Travel Assistant";
      case "/planner":
        return "Smart Planner";
      case "/saved":
        return "My Saved Escapes";
      case "/profile":
        return "Profile & Settings";
      default:
        return "Tourist.AI";
    }
  };

  return (
    <header className="h-16 bg-white/80 dark:bg-[#111827]/85 backdrop-blur-md border-b border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between px-5 sticky top-0 z-10">
      <div className="flex items-center gap-3">
        {/* Hamburger Menu for Tablet (sm to lg) */}
        <button
          onClick={onMenuClick}
          className="hidden sm:inline-flex lg:hidden p-2 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          aria-label="Toggle Navigation Drawer"
        >
          <Menu className="w-5.5 h-5.5" />
        </button>

        {/* Small screen mobile logo */}
        <div className="flex sm:hidden items-center justify-center w-8 h-8 rounded-lg bg-teal-600 text-white shadow-sm shadow-teal-600/10 mr-1">
          <Sparkles className="w-4.5 h-4.5" />
        </div>

        <div>
          <h2 className="font-heading text-base sm:text-lg font-bold text-slate-800 dark:text-slate-100 leading-tight">
            {getPageTitle()}
          </h2>
          <p className="hidden sm:block text-[10px] text-slate-400 font-medium">
            Discover. Plan. Explore.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* AI Agents sync indicator */}
        <div className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-teal-50 dark:bg-teal-950/20 border border-teal-100/50 dark:border-teal-900/30 text-[10.5px] font-semibold text-teal-700 dark:text-teal-400">
          <Wifi className="w-3.5 h-3.5 animate-pulse" />
          <span>AI Core Online</span>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all hover:scale-105"
          aria-label="Toggle Theme"
        >
          {theme === "light" ? <Moon className="w-4.5 h-4.5" /> : <Sun className="w-4.5 h-4.5" />}
        </button>

        {/* User profile image shortcut for tablet/mobile */}
        <div className="lg:hidden flex items-center">
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
            alt="Profile Avatar"
            className="w-8 h-8 rounded-full object-cover border border-slate-200 dark:border-slate-800 shadow-sm"
          />
        </div>
      </div>
    </header>
  );
};
export default TopBar;
