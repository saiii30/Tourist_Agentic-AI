import React from "react";
import type { TrainBetweenStations } from "../types/railradar"

const DAYS: { key: string; label: string }[] = [
    { key: "mon", label: "Mon" },
    { key: "tue", label: "Tue" },
    { key: "wed", label: "Wed" },
    { key: "thu", label: "Thu" },
    { key: "fri", label: "Fri" },
    { key: "sat", label: "Sat" },
    { key: "sun", label: "Sun" },
];

function formatDuration(minutes: number) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h}h ${m}m`;
}

interface TrainCardProps {
    entry: TrainBetweenStations;
    fromCode: string;
    toCode: string;
    fromName: string;
    toName: string;
    /** JS getDay() style but 0=Mon..6=Sun to match runDays; pass the weekday of the selected search date */
    selectedDayKey: string;
    onClick?: () => void;
}

export const TrainCard: React.FC<TrainCardProps> = ({
    entry,
    fromCode,
    toCode,
    fromName,
    toName,
    selectedDayKey,
    onClick,
}) => {
    const runsToday = entry.train.runDays.includes(selectedDayKey as any);

    return (
        <button
            type="button"
            onClick={onClick}
            className="flex w-full flex-col rounded-xl border border-slate-700/70 bg-slate-900/60 p-4 text-left shadow-sm transition-colors hover:border-emerald-600/50"
        >
            <div className="mb-3 flex items-center gap-2">
                <span className="rounded bg-emerald-950/70 px-2 py-0.5 text-xs font-bold text-emerald-400">
                    {entry.train.number}
                </span>
                <h4 className="truncate text-sm font-bold text-slate-100">{entry.train.name}</h4>
            </div>

            <div className="mb-1 flex items-center justify-between">
                <div>
                    <div className="text-base font-bold text-slate-100">{entry.from.departure}</div>
                </div>
                <div className="flex flex-col items-center px-2">
                    <span className="text-xs font-semibold text-slate-400">{formatDuration(entry.duration)}</span>
                </div>
                <div>
                    <div className="text-base font-bold text-slate-100">{entry.to.arrival}</div>
                </div>
            </div>

            <div className="mb-3 flex items-start justify-between gap-2 text-[11px] text-slate-500">
                <span className="max-w-[40%] truncate">
                    {fromCode} - {fromName}
                </span>
                <span className="whitespace-nowrap font-medium text-slate-400">{entry.distance} km</span>
                <span className="max-w-[40%] truncate text-right">
                    {toCode} - {toName}
                </span>
            </div>

            <div className="mb-1 grid grid-cols-7 gap-1">
                {DAYS.map((d) => {
                    const active = entry.train.runDays.includes(d.key as any);
                    const isSelected = d.key === selectedDayKey;
                    return (
                        <span
                            key={d.key}
                            className={`rounded-md py-1 text-center text-[10px] font-semibold ${active
                                    ? isSelected
                                        ? "bg-emerald-600 text-white ring-2 ring-emerald-400"
                                        : "bg-emerald-950/70 text-emerald-300"
                                    : "bg-slate-800/60 text-slate-500"
                                }`}
                        >
                            {d.label}
                        </span>
                    );
                })}
            </div>

            {!runsToday && (
                <span className="mt-1 text-[11px] font-semibold text-amber-500">Not running on selected date</span>
            )}

            {entry.live && (
                <div className="mt-2 border-t border-slate-800 pt-2 text-[11px] text-slate-400">
                    {entry.live.type === "running" && entry.live.delayMinutes !== undefined && (
                        <span
                            className={entry.live.delayMinutes > 0 ? "text-amber-400" : "text-emerald-400"}
                        >
                            {entry.live.delayMinutes > 0
                                ? `Running ${entry.live.delayMinutes} min late`
                                : "Running on time"}
                            {entry.live.platform ? ` · Platform ${entry.live.platform}` : ""}
                        </span>
                    )}
                    {entry.live.type === "upcoming" && (
                        <span>
                            Scheduled{entry.live.platform ? ` · Platform ${entry.live.platform}` : ""}
                        </span>
                    )}
                </div>
            )}
        </button>
    );
};
