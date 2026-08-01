import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Train, ExternalLink, ShieldAlert, Clock, Calendar } from "lucide-react";
import axios from "axios";
import { apiUrl } from "../api/config";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export const TrainSearchResults: React.FC = () => {
  const { from, to } = useParams<{ from: string; to: string }>();
  const [searchParams] = useSearchParams();
  const date = searchParams.get("date") || todayISO();
  const navigate = useNavigate();

  const fromName = searchParams.get("fromName") || from || "";
  const toName = searchParams.get("toName") || to || "";

  const [trains, setTrains] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  useEffect(() => {
    if (!from || !to) return;

    setLoading(true);
    setError(null);
    setCurrentPage(1);

    axios.get(apiUrl("/api/trains/between"), {
      params: {
        from: from,
        to: to,
        date: date
      }
    })
      .then((res) => {
        if (res.data && res.data.success) {
          setTrains(res.data.data?.trains || []);
        } else {
          setError("Failed to fetch train schedules.");
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to contact search backend.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [from, to, date]);

  const formatConfirmTktDate = (dateStr: string) => {
    if (!dateStr) return "";
    const parts = dateStr.split("-");
    if (parts.length !== 3) return "";
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  };

  const handleBookRedirect = () => {
    if (!from || !to) return;
    const formattedDate = formatConfirmTktDate(date);
    const queryUrl = `https://www.confirmtkt.com/rbooking/trains/from/${from.toUpperCase()}/to/${to.toUpperCase()}/${formattedDate}`;
    window.open(queryUrl, "_blank");
  };

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentTrains = trains.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(trains.length / itemsPerPage);

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200 text-left pb-16">
      {/* Route Breadcrumb Header */}
      <div className="flex items-center justify-between bg-emerald-600 px-6 py-3 shadow-md">
        <div className="flex items-center gap-3 text-sm font-semibold text-white">
          <button onClick={() => navigate("/trains")} aria-label="Go back" className="hover:opacity-85">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <span className="flex items-center gap-1.5 font-heading capitalize">
            <Train className="h-4 w-4" />
            Trains: {fromName} ⇄ {toName}
          </span>
          <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-mono">
            {date}
          </span>
        </div>
      </div>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {/* Prominent ConfirmTkt search card */}
        <div className="mb-6 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Train className="h-4 w-4 text-emerald-400" />
            Search Directly on ConfirmTkt
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed capitalize">
            Click below to open ConfirmTkt with your pre-filled search for{" "}
            <span className="font-bold text-slate-200">{fromName} ⇄ {toName}</span>.
          </p>
          <button
            onClick={handleBookRedirect}
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors"
          >
            Search on ConfirmTkt
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Train className="h-5 w-5 text-emerald-400" />
              Available Trains
            </h2>
            <p className="text-xs text-slate-450 mt-1">
              Found {trains.length} schedules {trains.length > 0 && `(showing page ${currentPage} of ${totalPages})`}
            </p>
          </div>
        </div>

        {/* LOADING & ERROR STATES */}
        {loading && (
          <div className="flex h-64 flex-col items-center justify-center gap-4">
            <svg className="animate-spin h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-sm font-semibold text-slate-400">Loading train options…</span>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-500/20 bg-red-950/10 p-5 text-center my-8">
            <ShieldAlert className="mx-auto h-10 w-10 text-red-500 mb-3" />
            <h4 className="text-sm font-bold text-slate-200">Unable to load live train schedules</h4>
            <p className="text-xs text-slate-450 mt-1">{error}</p>
          </div>
        )}

        {/* RESULTS LIST */}
        {!loading && !error && trains.length === 0 && (
          <p className="py-16 text-center text-sm text-slate-500">No trains found matching this query.</p>
        )}

        {!loading && !error && trains.length > 0 && (
          <div className="space-y-3">
            {currentTrains.map((t, idx) => {
              const durationMins = t.duration || 0;
              const durationStr = `${Math.floor(durationMins / 60)}h ${durationMins % 60}m`;
              return (
                <div 
                  key={idx}
                  className="rounded-xl border border-slate-700/60 bg-slate-900/60 p-4 flex items-center justify-between gap-4 hover:border-emerald-600/30 transition-all shadow-sm"
                >
                  <div className="flex-1 min-w-0 space-y-2">
                    {/* Train Info */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="rounded-md bg-emerald-950/70 p-1.5 text-emerald-400">
                        <Train className="h-4 w-4" />
                      </span>
                      <span className="font-heading font-bold text-sm text-slate-100 truncate">
                        {t.train?.name} ({t.train?.number})
                      </span>
                      <span className="rounded bg-emerald-950/60 px-1.5 py-0.5 text-[10px] font-bold text-emerald-400">
                        {t.train?.type}
                      </span>
                    </div>

                    {/* Times & Duration */}
                    <div className="flex items-center justify-between pr-4 max-w-sm">
                      <div>
                        <span className="text-xs text-slate-500 block">Departure</span>
                        <span className="text-sm font-semibold text-slate-200">{t.from?.departure}</span>
                      </div>
                      
                      <div className="flex flex-col items-center">
                        <span className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {durationStr}
                        </span>
                        <div className="h-px w-16 bg-slate-800 my-1 relative">
                          <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-1.5 w-1.5 rounded-full bg-slate-600" />
                        </div>
                        <span className="text-[9px] text-slate-550 font-bold">
                          {t.distance} km | {t.totalHaltsBetween} halts
                        </span>
                      </div>

                      <div>
                        <span className="text-xs text-slate-500 block">Arrival</span>
                        <span className="text-sm font-semibold text-slate-200">{t.to?.arrival}</span>
                      </div>
                    </div>

                    {/* Run Days */}
                    {t.train?.runDays && t.train?.runDays.length > 0 && (
                      <div className="text-[10px] text-slate-500 font-medium flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-500" />
                        <span>Runs: <span className="text-slate-300 capitalize">{t.train.runDays.join(", ")}</span></span>
                      </div>
                    )}
                  </div>

                  {/* Book Button */}
                  <div className="text-right border-l border-slate-800 pl-4 flex flex-col justify-center items-end min-w-[100px] h-20">
                    <button
                      onClick={handleBookRedirect}
                      className="flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 transition-colors"
                    >
                      Book
                      <ExternalLink className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* PAGINATION CONTROLS */}
        {!loading && !error && trains.length > itemsPerPage && (
          <div className="mt-8 flex items-center justify-between border-t border-slate-800 pt-6">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="rounded-lg bg-slate-900 border border-slate-700/60 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-850 disabled:opacity-50 disabled:hover:bg-slate-900 transition-colors cursor-pointer"
            >
              Previous
            </button>
            <div className="flex items-center gap-1.5">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNumber) => (
                <button
                  key={pageNumber}
                  onClick={() => setCurrentPage(pageNumber)}
                  className={`h-8 w-8 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                    currentPage === pageNumber
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-900 border border-slate-700/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                  }`}
                >
                  {pageNumber}
                </button>
              ))}
            </div>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="rounded-lg bg-slate-900 border border-slate-700/60 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-850 disabled:opacity-50 disabled:hover:bg-slate-900 transition-colors cursor-pointer"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default TrainSearchResults;
