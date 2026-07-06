import { useEffect, useState } from "react";

type Crowd = {
  level: "Very High" | "High" | "Medium" | "Low";
  emoji: string;
  score: number;
  maxscore: number;
  reasons: string[];
  advice: string;
  weather: { condition: string; temperature: number; humidity: number };
  updatedat: number;
  nextrefresh: number;
};

const COLORS: Record<string, string> = {
  "Very High": "#dc2626",
  High: "#f97316",
  Medium: "#eab308",
  Low: "#16a34a",
};

export default function CrowdMeter({
  city,
  attraction,
}: {
  city: string;
  attraction: string;
}) {
  const [data, setData] = useState<Crowd | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      const r = await fetch(
        `/api/crowd?city=${encodeURIComponent(city)}&attraction=${encodeURIComponent(attraction)}`
      );
      if (!r.ok) throw new Error(await r.text());
      setData(await r.json());
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 30 * 60 * 1000); // 30 min
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city, attraction]);

  if (err) return <div className="text-xs text-red-500">Crowd unavailable</div>;
  if (!data) return <div className="text-xs text-gray-400">Loading crowd…</div>;

  const pct = Math.min(100, Math.round((data.score / data.maxscore) * 100));
  const color = COLORS[data.level] || "#6b7280";

  return (
    <div className="rounded-2xl border border-gray-200 p-4 bg-white shadow-sm w-full max-w-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-gray-700">Live Crowd</div>
        <div className="text-xs text-gray-400">
          updated {new Date(data.updatedat * 1000).toLocaleTimeString()}
        </div>
      </div>

      {/* gauge bar */}
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
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${pct}%`, backgroundColor: color }}
            />
          </div>
        </div>
      </div>

      {/* why */}
      <div className="mt-3">
        <div className="text-xs uppercase tracking-wide text-gray-400 mb-1">
          Why
        </div>
        <div className="flex flex-wrap gap-1.5">
          {data.reasons.map((r) => (
            <span
              key={r}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700"
            >
              {r}
            </span>
          ))}
        </div>
      </div>

      {/* advice */}
      <div className="mt-3 text-xs text-gray-600 flex gap-1.5">
        <span>💡</span>
        <span>{data.advice}</span>
      </div>

      {/* weather footer */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-500">
        <span>🌤 {data.weather.condition}</span>
        <span>{Math.round(data.weather.temperature)}°C</span>
        <span>💧 {data.weather.humidity}%</span>
      </div>
    </div>
  );
}
