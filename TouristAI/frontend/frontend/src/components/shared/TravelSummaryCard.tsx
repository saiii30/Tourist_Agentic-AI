import React, { useState } from "react";
import { Calendar, Users, DollarSign, Compass, Sun, HelpCircle, ChevronRight, ShieldAlert } from "lucide-react";
import type { TripDetails } from "../../context/TravelPlannerContext";

interface TravelSummaryCardProps {
  trip: TripDetails;
}

export const TravelSummaryCard: React.FC<TravelSummaryCardProps> = ({ trip }) => {
  const [showPacking, setShowPacking] = useState(false);

  const getTempAndCondition = (summary: string) => {
    if (!summary) return { temp: "26°C", condition: "Warm, Sunny" };
    const tempMatch = summary.match(/(\d+(?:\.\d+)?)\s*°C/);
    const temp = tempMatch ? `${tempMatch[1]}°C` : "26°C";
    const condMatch = summary.match(/with\s+([^.\n]+)/);
    const condition = condMatch ? condMatch[1].trim() : "Warm, Sunny";
    return { temp, condition };
  };
  const { temp: tempVal, condition: condVal } = getTempAndCondition(trip.weatherSummary);

  return (
    <div className="relative rounded-[28px] overflow-hidden shadow-lg border border-slate-200/50 dark:border-slate-800/80 bg-white dark:bg-[#111827]">
      
      {/* 1. Large Hero Banner Image */}
      <div className="relative h-48 sm:h-64 w-full bg-slate-100 dark:bg-slate-800">
        <img
          src={trip.bannerImage}
          alt={trip.cityName}
          className="w-full h-full object-cover"
        />
        {/* Soft dark overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/40 to-transparent" />
        
        {/* City Info Overlay */}
        <div className="absolute bottom-6 left-6 right-6 text-white text-left space-y-1">
          <span className="text-[10px] sm:text-[11px] font-bold text-teal-350 dark:text-teal-400 bg-teal-650/40 backdrop-blur-md px-3 py-1 rounded-full border border-teal-500/20 uppercase tracking-widest">
            AI Generated Plan
          </span>
          <h1 className="font-heading text-2xl sm:text-4xl font-extrabold tracking-tight">
            {trip.cityName}
          </h1>
          <p className="text-xs sm:text-sm font-medium text-slate-200 flex items-center gap-1.5 opacity-90">
            <Calendar className="w-4 h-4 text-slate-300" />
            <span>{trip.startDate} — {trip.endDate}</span>
            <span>·</span>
            <span>{trip.durationDays} Days</span>
          </p>
        </div>
      </div>

      {/* 2. Floating Info Grid (Glassmorphism & Flex layout) */}
      <div className="p-5 sm:p-6 grid grid-cols-2 md:grid-cols-5 gap-3 bg-slate-50/50 dark:bg-slate-900/40 border-b border-slate-100 dark:border-slate-800">
        
        {/* Travelers */}
        <div className="p-3 rounded-2xl bg-white dark:bg-[#1e293b]/60 border border-slate-250/40 dark:border-slate-800/60 text-left space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            Travelers
          </span>
          <p className="text-xs font-bold text-slate-800 dark:text-slate-250 flex items-center gap-1.5">
            <Users className="w-4 h-4 text-teal-605" />
            {trip.travelersCount} Guests
          </p>
        </div>

        {/* Budget */}
        <div className="p-3 rounded-2xl bg-white dark:bg-[#1e293b]/60 border border-slate-250/40 dark:border-slate-800/60 text-left space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            Budget Tier
          </span>
          <p className="text-xs font-bold text-slate-800 dark:text-slate-250 flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-teal-605" />
            {trip.budget}
          </p>
        </div>

        {/* Style */}
        <div className="p-3 rounded-2xl bg-white dark:bg-[#1e293b]/60 border border-slate-250/40 dark:border-slate-800/60 text-left space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            Travel Style
          </span>
          <p className="text-xs font-bold text-slate-800 dark:text-slate-250 flex items-center gap-1.5">
            <Compass className="w-4.5 h-4.5 text-teal-605" />
            {trip.travelStyle}
          </p>
        </div>

        {/* Cost estimate */}
        <div className="p-3 rounded-2xl bg-white dark:bg-[#1e293b]/60 border border-slate-250/40 dark:border-slate-800/60 text-left space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            Est. Expenses
          </span>
          <p className="text-xs font-extrabold text-teal-700 dark:text-teal-400 flex items-center gap-1">
            <span className="font-bold text-sm">₹</span>
            <span>{typeof trip.estimatedCost === 'number' ? trip.estimatedCost.toLocaleString('en-IN') : trip.estimatedCost} INR</span>
          </p>
        </div>

        {/* Weather Indicator */}
        <div className="col-span-2 md:col-span-1 p-3 rounded-2xl bg-white dark:bg-[#1e293b]/60 border border-slate-250/40 dark:border-slate-800/60 text-left space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            Forecast
          </span>
          <p className="text-xs font-bold text-slate-800 dark:text-slate-250 flex items-center gap-1.5 capitalize">
            <Sun className="w-4 h-4 text-amber-500 animate-spin-slow" />
            {tempVal} {condVal}
          </p>
        </div>

      </div>

      {/* 3. Dropdowns details for Weather Summary & Packing Tips */}
      <div className="p-5 sm:p-6 space-y-4">
        
        {/* Packing Checklist Toggle */}
        <div className="border border-slate-200 dark:border-slate-800/80 rounded-2xl overflow-hidden">
          <button
            onClick={() => setShowPacking(!showPacking)}
            className="w-full flex items-center justify-between p-4 bg-slate-50/50 dark:bg-slate-900/20 text-left"
          >
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4.5 h-4.5 text-slate-400" />
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                Recommended Packing Tips & Preparation
              </span>
            </div>
            <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${showPacking ? "rotate-90" : ""}`} />
          </button>

          {showPacking && (
            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-[#111827] text-left">
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {trip.packingTips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-650 dark:text-slate-400 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-650 bg-teal-500 flex-shrink-0 mt-1.5" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Quick Weather Forecast Strip */}
        <div className="flex items-start gap-3 p-3 bg-amber-50/50 dark:bg-amber-950/10 rounded-2xl border border-amber-100/50 dark:border-amber-950/20 text-left">
          <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider block">
              Weather Warning Forecast
            </span>
            <p className="text-[11.5px] font-semibold text-slate-600 dark:text-slate-450 leading-snug">
              {trip.weatherSummary}
            </p>
          </div>
        </div>

      </div>

    </div>
  );
};
export default TravelSummaryCard;
