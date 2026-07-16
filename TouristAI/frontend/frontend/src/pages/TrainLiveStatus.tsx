import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Train, MapPin, Clock, AlertTriangle } from "lucide-react";
import { railradarApi } from "../api/railradarApi";

interface Stop {
  station: string;
  station_name: string;
  arrival: string;
  departure: string;
  halt: number;
  day: number;
  sequence: number;
}

interface TrainDetails {
  number: string;
  name: string;
  type: string;
  runDays: string[];
  stops?: Stop[];
}

interface LiveStatus {
  type: string;
  startDate: string;
  expectedArrivalTime?: string;
  expectedDepartureTime?: string;
  platform?: string;
  delayMinutes?: number;
  currentStation?: string;
  lastUpdated?: string;
}

export const TrainLiveStatus: React.FC = () => {
  const { number } = useParams<{ number: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [details, setDetails] = useState<TrainDetails | null>(null);
  const [live, setLive] = useState<LiveStatus | null>(null);

  useEffect(() => {
    if (!number) return;

    setLoading(true);
    setError(null);

    Promise.all([
      railradarApi.getTrainDetails(number),
      railradarApi.getTrainLiveStatus(number)
    ])
      .then(([detailsRes, liveRes]) => {
        setDetails(detailsRes as any);
        setLive(liveRes as any);
      })
      .catch((err) => {
        setError(err.message || "Failed to load train details.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [number]);

  if (loading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3">
        <svg className="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm font-semibold text-slate-400">Fetching live status…</span>
      </div>
    );
  }

  if (error || !details) {
    return (
      <div className="mx-auto max-w-xl p-6 text-center">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-bold text-slate-100">Failed to load details</h3>
        <p className="text-sm text-slate-400 mt-2">{error || "Could not retrieve train timetable info."}</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-6 rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-blue-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  const delay = live?.delayMinutes || 0;
  const isLate = delay > 0;
  const currentStationCode = live?.currentStation?.toUpperCase() || "";

  return (
    <div className="mx-auto max-w-3xl p-4 sm:p-6 space-y-6 text-left pb-16">
      {/* Top Breadcrumb Header */}
      <div className="flex items-center gap-3 border-b border-slate-800/80 pb-5">
        <button
          onClick={() => navigate(-1)}
          className="rounded-full border border-slate-700 p-2 text-slate-300 hover:bg-slate-800"
          aria-label="Go back"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-blue-950/70 px-2 py-0.5 text-xs font-bold text-blue-400 font-mono">
              #{details.number}
            </span>
            <h1 className="font-heading text-lg sm:text-xl font-extrabold text-slate-100 tracking-tight leading-none">
              {details.name}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-medium capitalize">
            Type: {details.type || "Express"} · Runs: {details.runDays?.join(", ")}
          </p>
        </div>
      </div>

      {/* Live Status Card */}
      {live && (
        <div className={`rounded-2xl border p-5 shadow-sm ${
          isLate 
            ? "border-amber-600/30 bg-amber-950/10" 
            : "border-emerald-600/30 bg-emerald-950/10"
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider ${
                isLate ? "bg-amber-600" : "bg-emerald-600"
              }`}>
                {live.type}
              </span>
              <h2 className="text-lg font-bold text-slate-100 mt-1">
                {isLate ? `Delayed by ${delay} mins` : "Running on Time"}
              </h2>
              {live.currentStation && (
                <p className="text-sm text-slate-300 flex items-center gap-1.5 font-medium">
                  <MapPin className="h-4 w-4 text-blue-400" />
                  Currently at: <span className="font-bold text-white">{details.stops?.find(s => s.station === currentStationCode)?.station_name || currentStationCode}</span>
                </p>
              )}
            </div>
            
            <div className="text-right border-t border-slate-800 pt-3 sm:border-0 sm:pt-0">
              <div className="text-xs text-slate-400 font-medium">Platform Info</div>
              <div className="text-2xl font-black text-slate-100 font-mono">Platform {live.platform || "N/A"}</div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5 flex items-center gap-1 justify-end">
                <Clock className="h-3 w-3" />
                Updated: {live.lastUpdated || "Just now"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TIMELINE TIMETABLE LIST */}
      <div className="bg-[#111827] border border-slate-800/80 rounded-2xl p-5 shadow-sm">
        <h3 className="text-base font-bold text-slate-100 mb-6 flex items-center gap-2">
          <Train className="h-5 w-5 text-blue-400" />
          Schedule &amp; Halts
        </h3>

        <div className="relative pl-8 space-y-8">
          {/* Vertical dashed line */}
          <div className="absolute left-[11px] top-3 bottom-3 w-px border-l border-dashed border-slate-700" />

          {details.stops && details.stops.map((stop, index) => {
            const isCurrent = stop.station === currentStationCode;
            
            return (
              <div key={stop.station} className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                {/* Node marker */}
                <span className={`absolute left-[-26px] top-1.5 h-3.5 w-3.5 rounded-full border-2 transition-all ${
                  isCurrent
                    ? "bg-blue-500 border-white ring-4 ring-blue-500/20 scale-125 z-10 animate-pulse"
                    : "bg-[#0b0f19] border-slate-700"
                }`} />

                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-heading font-bold text-sm sm:text-base text-slate-100">
                      {stop.station_name}
                    </span>
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-bold text-slate-400 uppercase font-mono">
                      {stop.station}
                    </span>
                  </div>
                  <div className="text-xs text-slate-450 font-medium">
                    Halt: {stop.halt > 0 ? `${stop.halt} mins` : index === 0 ? "Origin" : "Destination"} · Day {stop.day}
                  </div>
                </div>

                {/* Timing info */}
                <div className="flex gap-4 sm:text-right text-xs text-slate-400 font-medium">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Arrival</span>
                    <span className="font-semibold text-slate-200 font-mono text-sm">{stop.arrival}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Departure</span>
                    <span className="font-semibold text-slate-200 font-mono text-sm">{stop.departure}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default TrainLiveStatus;
