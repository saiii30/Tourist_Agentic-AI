import React from "react";
import { Sun, Cloud, CloudRain, Wind, Droplets } from "lucide-react";

interface WeatherCardProps {
  location: string;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ location }) => {
  return (
    <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm text-left flex flex-col justify-between h-full">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100">
              Weather Widget
            </h4>
            <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
              {location}
            </p>
          </div>
          <span className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/20 text-amber-500">
            <Sun className="w-5 h-5 animate-spin-slow" />
          </span>
        </div>

        {/* Temperature layout */}
        <div className="flex items-baseline gap-1.5">
          <span className="font-heading text-3xl font-extrabold text-slate-800 dark:text-slate-105">
            28°C
          </span>
          <span className="text-xs text-slate-400 font-bold">
            Feels like 31°C
          </span>
        </div>

        {/* Detail statistics */}
        <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            <Droplets className="w-4 h-4 text-sky-500" />
            <span>Humid: 62%</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            <Wind className="w-4 h-4 text-teal-500" />
            <span>Wind: 14 km/h</span>
          </div>
        </div>
      </div>

      {/* 3 Day Outlook Mini Strip */}
      <div className="pt-3 mt-3 border-t border-slate-100 dark:border-slate-800 space-y-1.5">
        <span className="text-[10px] font-bold text-slate-450 uppercase tracking-widest block">
          3-Day Outlook
        </span>
        <div className="grid grid-cols-3 gap-1">
          <div className="text-center p-1 rounded-lg bg-slate-50 dark:bg-slate-900/40">
            <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block">Tue</span>
            <Sun className="w-4 h-4 text-amber-500 mx-auto my-1" />
            <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300">29°</span>
          </div>
          <div className="text-center p-1 rounded-lg bg-slate-50 dark:bg-slate-900/40">
            <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block">Wed</span>
            <Cloud className="w-4 h-4 text-slate-400 mx-auto my-1" />
            <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300">27°</span>
          </div>
          <div className="text-center p-1 rounded-lg bg-slate-50 dark:bg-slate-900/40">
            <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block">Thu</span>
            <CloudRain className="w-4 h-4 text-sky-400 mx-auto my-1" />
            <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300">25°</span>
          </div>
        </div>
      </div>

    </div>
  );
};
export default WeatherCard;
