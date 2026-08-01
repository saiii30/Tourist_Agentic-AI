// src/components/LoadingOverlay.tsx
import { useEffect, useState } from "react";
import { connectTripWS, AgentProgress } from "../api/trip";

interface Props {
  tripId: string;
}

export default function LoadingOverlay({ tripId }: Props) {
  const [progress, setProgress] = useState<Record<string, AgentProgress>>({});
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    const ws = connectTripWS(tripId, {
      onMessage: (msg) => {
        if (msg.type === "agent_progress") {
          setProgress((p) => ({
            ...p,
            [msg.agent]: { progress: msg.progress, state: "running" },
          }));
        } else if (msg.type === "agent_result") {
          setProgress((p) => ({
            ...p,
            [msg.agent]: { progress: 100, state: "done", payload: msg.payload },
          }));
        } else if (msg.type === "trip_complete") {
          setCompleted(true);
          ws.close();
        }
      },
    });
    return () => ws.close();
  }, [tripId]);

  if (completed) return null;

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 w-96 shadow-lg">
        <h2 className="text-xl font-semibold mb-4 text-primary-600">Building your itinerary…</h2>
        <ul className="space-y-3">
          {Object.entries(progress).map(([agent, data]) => (
            <li key={agent} className="flex items-center justify-between">
              <span className="capitalize">{agent}</span>
              <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary-500 h-full transition-all duration-300"
                  style={{ width: `${data.progress}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          You can close this window; the itinerary will appear in the “My Trips” section once ready.
        </p>
      </div>
    </div>
  );
}
