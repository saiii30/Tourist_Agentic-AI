import React, { useState, useEffect } from "react";
import { Users, Clock, Sparkles, TrendingUp, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import { apiUrl } from "../../api/config";

interface CrowdPredictionData {
  destination: string;
  city: string;
  date: string;
  target_hour: number;
  current_crowd_percentage: number;
  crowd_level: string;
  status_color: string;
  badge: string;
  recommended_window: string;
  active_festival?: string | null;
  is_weekend: boolean;
  advisory: string;
  hourly_forecast: number[];
}

interface CrowdDensityWidgetProps {
  destination: string;
  cityName?: string;
  dateStr?: string;
  timeStr?: string;
  category?: string;
  variant?: "default" | "floating";
}

const getCrowdStatus = (pct: number) => {
  if (pct >= 80) {
    return {
      label: "Overcrowded",
      color: "#ef4444",
      softBg: "rgba(239, 68, 68, 0.12)",
      textClass: "text-red-700 dark:text-red-300",
      borderClass: "border-red-200 dark:border-red-900/50",
    };
  }
  if (pct >= 60) {
    return {
      label: "Heavy",
      color: "#f97316",
      softBg: "rgba(249, 115, 22, 0.12)",
      textClass: "text-orange-700 dark:text-orange-300",
      borderClass: "border-orange-200 dark:border-orange-900/50",
    };
  }
  if (pct >= 35) {
    return {
      label: "Moderate",
      color: "#eab308",
      softBg: "rgba(234, 179, 8, 0.14)",
      textClass: "text-yellow-700 dark:text-yellow-300",
      borderClass: "border-yellow-200 dark:border-yellow-900/50",
    };
  }
  return {
    label: "Comfortable",
    color: "#22c55e",
    softBg: "rgba(34, 197, 94, 0.12)",
    textClass: "text-green-700 dark:text-green-300",
    borderClass: "border-green-200 dark:border-green-900/50",
  };
};

const CrowdRing: React.FC<{
  pct: number;
  color: string;
  size?: number;
  track?: string;
  textClass?: string;
}> = ({ pct, color, size = 72, track = "rgba(148, 163, 184, 0.22)", textClass = "text-slate-900 dark:text-white" }) => {
  const stroke = 7;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, pct)) / 100) * circumference;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg className="-rotate-90" width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={track}
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <span className={`text-sm font-black tabular-nums ${textClass}`}>{pct}%</span>
      </div>
    </div>
  );
};

export const CrowdDensityWidget: React.FC<CrowdDensityWidgetProps> = ({
  destination,
  cityName = "Madurai",
  dateStr,
  timeStr = "10:00",
  category = "temple",
  variant = "default"
}) => {
  const [prediction, setPrediction] = useState<CrowdPredictionData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [showHourlyGraph, setShowHourlyGraph] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    fetch(apiUrl("/predict-crowd"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        destination,
        city: cityName,
        date: dateStr,
        time: timeStr,
        category
      })
    })
      .then((res) => res.json())
      .then((data) => {
        if (isMounted && data.status === "success") {
          setPrediction(data.prediction);
        }
      })
      .catch((err) => {
        console.error("Crowd prediction error:", err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [destination, cityName, dateStr, timeStr, category]);

  if (loading) {
    if (variant === "floating") {
      return (
        <div className="rounded-2xl border border-white/15 bg-black/45 px-3 py-2.5 text-xs text-white shadow-lg backdrop-blur-md flex items-center gap-2 animate-pulse">
          <Users className="w-4 h-4 text-teal-300" />
          <span className="font-semibold">Predicting crowd for {destination}...</span>
        </div>
      );
    }

    return (
      <div className="p-3 bg-slate-50 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-800 rounded-xl text-xs flex items-center gap-2 animate-pulse">
        <Users className="w-4 h-4 text-teal-500" />
        <span className="text-slate-500 font-medium">Predicting crowd density for {destination}...</span>
      </div>
    );
  }

  if (!prediction) return null;

  const pct = prediction.current_crowd_percentage;
  const status = getCrowdStatus(pct);
  const detailPanel = (
    <div className="pointer-events-none absolute left-0 right-0 top-full z-30 mt-2 opacity-0 translate-y-1 transition-all duration-200 group-hover:pointer-events-auto group-hover:opacity-100 group-hover:translate-y-0 group-focus-within:pointer-events-auto group-focus-within:opacity-100 group-focus-within:translate-y-0">
      <div className="rounded-xl border border-slate-200 bg-white p-3 text-left shadow-xl dark:border-slate-800 dark:bg-slate-950">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-extrabold uppercase tracking-wide text-slate-400">Crowd details</p>
            <h6 className="mt-0.5 text-xs font-black text-slate-850 dark:text-slate-100">{destination}</h6>
          </div>
          <span
            className={`rounded-full border px-2 py-0.5 text-[10px] font-extrabold ${status.textClass} ${status.borderClass}`}
            style={{ backgroundColor: status.softBg }}
          >
            {status.label}
          </span>
        </div>
        <div className="mt-2 grid gap-1.5 text-[10.5px] font-semibold text-slate-600 dark:text-slate-300">
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-teal-500" />
            Quiet window: <b>{prediction.recommended_window}</b>
          </span>
          <span>{prediction.is_weekend ? "Weekend traffic expected" : "Weekday pattern expected"}</span>
          {prediction.active_festival && <span>Festival/Event: {prediction.active_festival}</span>}
          <p className="leading-snug text-slate-500 dark:text-slate-400">{prediction.advisory}</p>
        </div>
      </div>
    </div>
  );

  if (variant === "floating") {
    return (
      <div tabIndex={0} className="group relative rounded-2xl border border-white/15 bg-black/45 p-3 text-left text-white shadow-xl backdrop-blur-md outline-none ring-0 transition focus-visible:ring-2 focus-visible:ring-teal-300">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wide text-teal-200">
              <Users className="w-3.5 h-3.5" />
              Destination Crowd
            </div>
            <h5 className="mt-0.5 truncate text-sm font-black">
              {destination}
            </h5>
            <p className="mt-1 text-[10.5px] font-semibold text-slate-200">
              {status.label} • {prediction.recommended_window}
            </p>
          </div>
          <CrowdRing pct={pct} color={status.color} size={64} textClass="text-white" track="rgba(255,255,255,0.16)" />
        </div>
        {detailPanel}
      </div>
    );
  }

  return (
    <div tabIndex={0} className="group relative bg-white dark:bg-[#111827] border border-slate-200/70 dark:border-slate-800 rounded-xl p-3.5 text-left shadow-2xs outline-none transition focus-visible:ring-2 focus-visible:ring-teal-400">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <CrowdRing pct={pct} color={status.color} size={66} textClass={status.textClass} />
          <div>
            <h5 className="font-bold text-xs text-slate-800 dark:text-slate-200 truncate flex items-center gap-1">
              AI Crowd Density
              <Sparkles className="w-3 h-3 text-amber-500" />
            </h5>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">
              Est. for {timeStr} ({prediction.date})
            </p>
            <span
              className={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-[10px] font-extrabold ${status.textClass} ${status.borderClass}`}
              style={{ backgroundColor: status.softBg }}
            >
              {status.label}
            </span>
          </div>
        </div>
        <span className="hidden text-[10px] font-bold text-slate-400 sm:inline">
          Hover for details
        </span>
      </div>

      {/* Advisory & Recommended Quiet Hours Window */}
      <div className="mt-3 p-2 bg-teal-500/5 dark:bg-teal-950/20 border border-teal-200/50 dark:border-teal-900/40 rounded-lg space-y-1 text-[10.5px]">
        <div className="flex items-start gap-1.5">
          <Clock className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-700 dark:text-slate-300">Recommended Quiet Window: </span>
            <span className="font-extrabold text-teal-700 dark:text-teal-300">{prediction.recommended_window}</span>
          </div>
        </div>

        <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-tight">
          {prediction.advisory}
        </p>
      </div>

      {/* Toggle Hourly Graph */}
      <button
        onClick={() => setShowHourlyGraph(!showHourlyGraph)}
        className="w-full text-[10px] font-bold text-slate-500 dark:text-slate-400 hover:text-teal-600 dark:hover:text-teal-400 flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-800/80 transition-colors"
      >
        <span className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          {showHourlyGraph ? "Hide 24-Hour Crowd Forecast" : "View Hourly Crowd Trend Graph"}
        </span>
        <ChevronRight className={`w-3 h-3 transition-transform ${showHourlyGraph ? "rotate-90" : ""}`} />
      </button>

      {/* Hourly Bar Chart Forecast */}
      {showHourlyGraph && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="pt-2 space-y-1"
        >
          <div className="flex items-end gap-1 h-14 bg-slate-900/90 dark:bg-slate-950 p-2 rounded-lg overflow-x-auto border border-slate-800">
            {prediction.hourly_forecast.slice(6, 21).map((val, idx) => {
              const hourNum = idx + 6;
              const isTarget = hourNum === prediction.target_hour;
              const barColor = getCrowdStatus(val).color;

              return (
                <div key={hourNum} className="flex-1 flex flex-col items-center gap-1 group relative min-w-[14px]">
                  <div
                    style={{ height: `${Math.max(10, val)}%`, backgroundColor: barColor }}
                    className={`w-full rounded-t transition-all ${isTarget ? "ring-2 ring-white z-10 scale-110" : "opacity-80 group-hover:opacity-100"}`}
                  />
                  <span className={`text-[8px] font-bold ${isTarget ? "text-teal-300" : "text-slate-400"}`}>
                    {hourNum}h
                  </span>
                </div>
              );
            })}
          </div>
          <div className="flex items-center justify-between text-[9px] text-slate-400 px-1">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 inline-block"/> Green</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block"/> Yellow</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400 inline-block"/> Orange</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block"/> Red</span>
          </div>
        </motion.div>
      )}
      {detailPanel}
    </div>
  );
};

export default CrowdDensityWidget;
