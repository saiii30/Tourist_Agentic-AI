import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Plane, Info } from "lucide-react";

export const FlightSearchHome: React.FC = () => {
  const navigate = useNavigate();
  const [fromAirport, setFromAirport] = useState("");
  const [toAirport, setToAirport] = useState("");
  const [date, setDate] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fromAirport.trim() || !toAirport.trim() || !date) return;
    
    navigate(
      `/flights/between/${fromAirport.trim().toUpperCase()}/${toAirport.trim().toUpperCase()}?date=${date}`
    );
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200">
      <main className="mx-auto max-w-lg px-4 py-8 sm:py-16 text-left">
        {/* Header section */}
        <div className="mb-8 text-center sm:text-left">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-950/70 text-emerald-400 mb-4 shadow-md shadow-emerald-500/10">
            <Plane className="h-6 w-6" />
          </div>
          <h2 className="font-heading text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
            Google Flights Search
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Find and compare flight schedules, durations, and pricing using the live scraper.
          </p>
        </div>

        {/* Flight Search Form */}
        <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900/60 shadow-xl backdrop-blur-md">
          <div className="bg-gradient-to-r from-emerald-950/40 to-slate-900/0 px-5 py-4 border-b border-slate-800">
            <h3 className="text-sm font-bold text-slate-200">Search Live Flights</h3>
          </div>

          <form onSubmit={handleSearch} className="p-5 space-y-4">
            {/* From Airport Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                From Airport (IATA Code)
              </label>
              <input
                type="text"
                maxLength={3}
                value={fromAirport}
                onChange={(e) => setFromAirport(e.target.value)}
                placeholder="e.g. DEL, BOM, MAA"
                required
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-emerald-500 font-mono tracking-widest text-center"
              />
            </div>

            {/* To Airport Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                To Airport (IATA Code)
              </label>
              <input
                type="text"
                maxLength={3}
                value={toAirport}
                onChange={(e) => setToAirport(e.target.value)}
                placeholder="e.g. SFO, LHR, DXB"
                required
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-emerald-500 font-mono tracking-widest text-center"
              />
            </div>

            {/* Date Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Departure Date
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
              disabled={!fromAirport.trim() || !toAirport.trim() || !date}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Search Flights <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Tip Box */}
        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/30 p-4 flex gap-3 items-start">
          <Info className="h-5 w-5 text-emerald-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-450 leading-relaxed">
            Note: Live scraping launches a browser session on the backend to retrieve real-time flight charts from Google Flights. Scraping might take up to 10-15 seconds depending on network latency.
          </p>
        </div>
      </main>
    </div>
  );
};

export default FlightSearchHome;
