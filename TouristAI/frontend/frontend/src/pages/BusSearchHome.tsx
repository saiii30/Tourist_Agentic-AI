import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Bus, Info } from "lucide-react";

export const BusSearchHome: React.FC = () => {
  const navigate = useNavigate();
  const [fromCity, setFromCity] = useState("");
  const [toCity, setToCity] = useState("");
  const [date, setDate] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fromCity.trim() || !toCity.trim() || !date) return;
    
    navigate(
      `/buses/between/${fromCity.trim().toLowerCase()}/${toCity.trim().toLowerCase()}?date=${date}`
    );
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200">
      <main className="mx-auto max-w-lg px-4 py-8 sm:py-16 text-left">
        {/* Header section */}
        <div className="mb-8 text-center sm:text-left">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-950/70 text-emerald-400 mb-4 shadow-md shadow-emerald-500/10">
            <Bus className="h-6 w-6" />
          </div>
          <h2 className="font-heading text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
            Bus Ticket Search
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Search schedules, operator ratings, and prices across different travel routes.
          </p>
        </div>

        {/* Bus Search Form */}
        <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900/60 shadow-xl backdrop-blur-md">
          <div className="bg-gradient-to-r from-emerald-950/40 to-slate-900/0 px-5 py-4 border-b border-slate-800">
            <h3 className="text-sm font-bold text-slate-200">Search Live Bus Operators</h3>
          </div>

          <form onSubmit={handleSearch} className="p-5 space-y-4">
            {/* From City Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                From City
              </label>
              <input
                type="text"
                value={fromCity}
                onChange={(e) => setFromCity(e.target.value)}
                placeholder="e.g. Chennai, Bangalore, Delhi"
                required
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-emerald-500"
              />
            </div>

            {/* To City Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                To City
              </label>
              <input
                type="text"
                value={toCity}
                onChange={(e) => setToCity(e.target.value)}
                placeholder="e.g. Madurai, Coimbatore, Mumbai"
                required
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-emerald-500"
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
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 placeholder-slate-555 outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!fromCity.trim() || !toCity.trim() || !date}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Search Buses <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Tip Box */}
        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/30 p-4 flex gap-3 items-start">
          <Info className="h-5 w-5 text-emerald-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-450 leading-relaxed">
            Note: Selecting a bus card redirects you directly to RedBus search with your route parameters. RedBus lets you pick specific seats and complete your booking online.
          </p>
        </div>
      </main>
    </div>
  );
};

export default BusSearchHome;
