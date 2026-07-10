import { useEffect, useState } from "react";

type CityCrowd = {
  city: string;
  level: "Very High" | "High" | "Medium" | "Low";
  emoji: string;
  score: number;
  maxscore: number;
  expectedVisitors: number;
  sampleCount: number;
  hourBand: string;
  reasons: string[];
  advice: string;
  updatedat: number;
};

const COLORS: Record<string, string> = {
  "Very High": "#dc2626",
  High: "#f97316",
  Medium: "#eab308",
  Low: "#16a34a",
};

export default function CityCrowdMeter({ city }: { city: string }) {
  const [data, setData] = useState<CityCrowd | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!city) return;

    const loadCityCrowd = async () => {
      try {
        const response = await fetch(
          `/api/city-crowd?city=${encodeURIComponent(city)}`
        );
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.detail || "City crowd data unavailable");
        }

        setData(payload);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "City crowd data unavailable"
        );
      }
    };

    loadCityCrowd();
  }, [city]);

  if (error) {
    return <p className="text-xs text-red-500 p-4">{error}</p>;
  }

  if (!data) {
    return <p className="text-xs text-slate-400 p-4">Loading city crowd…</p>;
  }

  const percentage = Math.min(
    100,
    Math.round((data.score / data.maxscore) * 100)
  );
  const color = COLORS[data.level] || "#6b7280";

  return (
    <div className="rounded-2xl border border-gray-200 p-4 bg-white shadow-sm w-full">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-700">
          {data.city} Overall Crowd
        </h4>
        <span className="text-xs text-gray-400">
          {new Date(data.updatedat * 1000).toLocaleTimeString()}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-2xl">{data.emoji}</span>

        <div className="flex-1">
          <div className="flex justify-between text-xs mb-1">
            <span className="font-medium" style={{ color }}>
              {data.level}
            </span>
            <span className="text-gray-500">
              {data.score}/{data.maxscore}
            </span>
          </div>

          <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${percentage}%`, backgroundColor: color }}
            />
          </div>
        </div>
      </div>

      <div className="mt-3 text-xs text-slate-600">
        Estimated historical visitors now:{" "}
        <strong>{data.expectedVisitors.toLocaleString()}</strong>
      </div>

      <div className="mt-3">
        <p className="text-xs uppercase tracking-wide text-gray-400 mb-1">
          Why
        </p>

        <div className="flex flex-wrap gap-1.5">
          {data.reasons.map((reason) => (
            <span
              key={reason}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700"
            >
              {reason}
            </span>
          ))}
        </div>
      </div>

      <p className="mt-3 text-xs text-gray-600">💡 {data.advice}</p>
    </div>
  );
}