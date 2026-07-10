import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Train, Info } from "lucide-react";
import { StationAutocomplete } from "../components/StationAutocomplete";
import type { Station } from "../types/railradar";

export const TrainSearchHome: React.FC = () => {
  const navigate = useNavigate();
  const [fromStation, setFromStation] = useState<Station | null>(null);
  const [toStation, setToStation] = useState<Station | null>(null);
  const [date, setDate] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fromStation || !toStation || !date) return;
    
    navigate(
      `/trains/between/${fromStation.code}/${toStation.code}?date=${date}&fromName=${encodeURIComponent(fromStation.name)}&toName=${encodeURIComponent(toStation.name)}`
    );
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200">
      <main className="mx-auto max-w-lg px-4 py-8 sm:py-16 text-left">
        {/* Header section */}
        <div className="mb-8 text-center sm:text-left">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-950/70 text-emerald-400 mb-4 shadow-md shadow-emerald-500/10">
            <Train className="h-6 w-6" />
          </div>
          <h2 className="font-heading text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
            Train Ticket Search
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Search seat availability, schedules, and train fares across routes.
          </p>
        </div>

        {/* Train Search Form */}
        <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900/60 shadow-xl backdrop-blur-md">
          <div className="bg-gradient-to-r from-emerald-950/40 to-slate-900/0 px-5 py-4 border-b border-slate-800">
            <h3 className="text-sm font-bold text-slate-200">Search Live Trains</h3>
          </div>

          <form onSubmit={handleSearch} className="p-5 space-y-4">
            {/* From Station Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                From Station
              </label>
              <StationAutocomplete
                label="Select origin station"
                value={fromStation}
                onChange={setFromStation}
                markerColor="green"
              />
            </div>

            {/* To Station Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                To Station
              </label>
              <StationAutocomplete
                label="Select destination station"
                value={toStation}
                onChange={setToStation}
                markerColor="blue"
              />
            </div>

            {/* Date Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Travel Date
              </label>
              <div className="relative">
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  required
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 placeholder-slate-550 outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!fromStation || !toStation || !date}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Search Trains <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Tip Box */}
        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/30 p-4 flex gap-3 items-start">
          <Info className="h-5 w-5 text-emerald-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-455 leading-relaxed">
            Note: Clicking any train schedule card redirects you directly to ConfirmTkt search to choose ticket classes and complete booking.
          </p>
        </div>
      </main>
    </div>
  );
};

export default TrainSearchHome;
