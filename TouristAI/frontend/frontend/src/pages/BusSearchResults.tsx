import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Bus, Clock, ExternalLink, ShieldAlert, Star } from "lucide-react";
import axios from "axios";

interface BusItem {
  operator: string;
  type: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  price: string;
  rating: string;
}

export const BusSearchResults: React.FC = () => {
  const { from, to } = useParams<{ from: string; to: string }>();
  const [searchParams] = useSearchParams();
  const date = searchParams.get("date") || "";
  const navigate = useNavigate();

  const [buses, setBuses] = useState<BusItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!from || !to || !date) return;

    setLoading(true);
    setError(null);

    axios.get(`/api/buses/search`, {
      params: {
        from: from,
        to: to,
        date: date
      }
    })
      .then((res) => {
        if (res.data && res.data.success) {
          setBuses(res.data.data || []);
        } else {
          setError("Failed to fetch bus schedules.");
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to contact search backend.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [from, to, date]);

  const formatRedbusDate = (dateStr: string) => {
    if (!dateStr) return "";
    const parts = dateStr.split("-");
    if (parts.length !== 3) return "";
    const year = parts[0];
    const monthIdx = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthName = months[monthIdx] || "";
    
    return `${day}-${monthName}-${year}`;
  };

  const handleBookRedirect = () => {
    // Generate standard slug-based RedBus booking URL to avoid form validation alerts
    // Spaces in city names (e.g. New Delhi) are replaced with hyphens
    const cleanFrom = (from || "").toLowerCase().trim().replace(/\s+/g, "-");
    const cleanTo = (to || "").toLowerCase().trim().replace(/\s+/g, "-");
    const formattedDate = formatRedbusDate(date);
    
    const queryUrl = `https://www.redbus.in/bus-tickets/${cleanFrom}-to-${cleanTo}${formattedDate ? `?doj=${formattedDate}` : ""}`;
    window.open(queryUrl, "_blank");
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200 text-left pb-16">
      {/* Route Breadcrumb Header */}
      <div className="flex items-center justify-between bg-emerald-600 px-6 py-3 shadow-md">
        <div className="flex items-center gap-3 text-sm font-semibold text-white">
          <button onClick={() => navigate("/buses")} aria-label="Go back" className="hover:opacity-85">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <span className="flex items-center gap-1.5 font-heading capitalize">
            <Bus className="h-4 w-4" />
            Buses: {from} ⇄ {to}
          </span>
          <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-mono">
            {date}
          </span>
        </div>
      </div>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {/* Prominent RedBus search card */}
        <div className="mb-6 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Bus className="h-4 w-4 text-emerald-400" />
            Search Directly on RedBus
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed capitalize">
            Click below to open RedBus with your pre-filled search for{" "}
            <span className="font-bold text-slate-200">{from} ⇄ {to}</span>.
          </p>
          <button
            onClick={handleBookRedirect}
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors"
          >
            Search on RedBus
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Bus className="h-5 w-5 text-emerald-400" />
              Available Buses
            </h2>
            <p className="text-xs text-slate-455 mt-1">
              Found {buses.length} schedules
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
            <span className="text-sm font-semibold text-slate-400">Loading bus options…</span>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-500/20 bg-red-950/10 p-5 text-center my-8">
            <ShieldAlert className="mx-auto h-10 w-10 text-red-500 mb-3" />
            <h4 className="text-sm font-bold text-slate-200">Unable to load buses</h4>
            <p className="text-xs text-slate-450 mt-1">{error}</p>
          </div>
        )}

        {/* RESULTS LIST */}
        {!loading && !error && buses.length === 0 && (
          <p className="py-16 text-center text-sm text-slate-500">No buses found matching this query.</p>
        )}

        {!loading && !error && buses.length > 0 && (
          <div className="space-y-3">
            {buses.map((bus, idx) => (
              <div 
                key={idx}
                className="rounded-xl border border-slate-700/60 bg-slate-900/60 p-4 flex items-center justify-between gap-4 hover:border-emerald-600/30 transition-all shadow-sm"
              >
                <div className="flex-1 min-w-0 space-y-2">
                  {/* Operator Info */}
                  <div className="flex items-center gap-2">
                    <span className="rounded-md bg-emerald-950/70 p-1.5 text-emerald-400">
                      <Bus className="h-4 w-4" />
                    </span>
                    <span className="font-heading font-bold text-sm text-slate-100 truncate">
                      {bus.operator}
                    </span>
                    <span className="flex items-center gap-0.5 rounded bg-emerald-950/60 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                      <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                      {bus.rating}
                    </span>
                  </div>

                  {/* Times & Duration */}
                  <div className="flex items-center justify-between pr-4 max-w-sm">
                    <div>
                      <span className="text-xs text-slate-500 block">Departure</span>
                      <span className="text-sm font-semibold text-slate-200">{bus.departure_time}</span>
                    </div>
                    
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {bus.duration}
                      </span>
                      <div className="h-px w-16 bg-slate-800 my-1 relative">
                        <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-1.5 w-1.5 rounded-full bg-slate-650" />
                      </div>
                      <span className="text-[9px] text-slate-550 font-bold text-center truncate max-w-[100px]" title={bus.type}>
                        {bus.type}
                      </span>
                    </div>

                    <div>
                      <span className="text-xs text-slate-500 block">Arrival</span>
                      <span className="text-sm font-semibold text-slate-200">{bus.arrival_time}</span>
                    </div>
                  </div>
                </div>

                {/* Price & Book Button */}
                <div className="text-right border-l border-slate-800 pl-4 flex flex-col justify-center items-end min-w-[100px] h-20">
                  <div className="text-[10px] text-slate-550 uppercase tracking-wider font-semibold">Fare</div>
                  <div className="text-lg font-black text-slate-100 font-mono mt-0.5">{bus.price}</div>
                  
                  <button
                    onClick={handleBookRedirect}
                    className="mt-2 flex items-center gap-1 rounded bg-emerald-600 px-2.5 py-1 text-[10px] font-bold text-white hover:bg-emerald-700 transition-colors"
                  >
                    Book
                    <ExternalLink className="h-2.5 w-2.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default BusSearchResults;
