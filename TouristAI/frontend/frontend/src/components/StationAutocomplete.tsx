import React, { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { railradarApi } from "../api/railradarApi"
import type { Station } from "../types/railradar"

interface StationAutocompleteProps {
    label: string;
    value: Station | null;
    onChange: (station: Station | null) => void;
    markerColor?: "green" | "blue";
    placeholder?: string;
}

export const StationAutocomplete: React.FC<StationAutocompleteProps> = ({
    label,
    value,
    onChange,
    markerColor = "blue",
    placeholder,
}) => {
    const [query, setQuery] = useState(value ? `${value.name} (${value.code})` : "");
    const [results, setResults] = useState<Station[]>([]);
    const [open, setOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setQuery(value ? `${value.name} (${value.code})` : "");
    }, [value]);

    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    useEffect(() => {
        if (!open || query.trim().length === 0) {
            setResults([]);
            return;
        }
        const timeout = setTimeout(async () => {
            try {
                const stations = await railradarApi.searchStations(query.trim());
                setResults(stations);
            } catch {
                setResults([]);
            }
        }, 250);
        return () => clearTimeout(timeout);
    }, [query, open]);

    const dotClass = markerColor === "green" ? "bg-emerald-500" : "bg-blue-500";

    return (
        <div ref={wrapperRef} className="relative flex items-center gap-3 py-3">
            <span className={`h-2.5 w-2.5 flex-shrink-0 rounded-full ${dotClass}`} />
            <input
                type="text"
                value={query}
                placeholder={placeholder || label}
                onFocus={() => setOpen(true)}
                onChange={(e) => {
                    setQuery(e.target.value);
                    setOpen(true);
                    if (value) onChange(null);
                }}
                className="w-full flex-1 bg-transparent text-sm font-medium text-slate-200 placeholder-slate-500 outline-none"
            />
            {query && (
                <button
                    type="button"
                    onClick={() => {
                        setQuery("");
                        onChange(null);
                    }}
                    className="text-slate-500 hover:text-slate-300"
                    aria-label={`Clear ${label}`}
                >
                    <X className="h-4 w-4" />
                </button>
            )}

            {open && results.length > 0 && (
                <div className="absolute left-0 right-0 top-full z-20 mt-1 max-h-64 overflow-y-auto rounded-lg border border-slate-700 bg-slate-800 shadow-xl">
                    {results.map((s) => (
                        <button
                            key={s.code}
                            type="button"
                            onClick={() => {
                                onChange(s);
                                setQuery(`${s.name} (${s.code})`);
                                setOpen(false);
                            }}
                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-200 hover:bg-slate-700"
                        >
                            <span className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px] font-bold text-blue-400">
                                {s.code}
                            </span>
                            <span className="truncate">{s.name}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};
