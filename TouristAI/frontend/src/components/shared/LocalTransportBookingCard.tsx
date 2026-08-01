import React from "react";
import { Bike, Bus, Car, ExternalLink, Navigation } from "lucide-react";

interface LocalTransportBookingCardProps {
  mode?: string;
  duration?: string;
  distance?: string;
  destination?: string;
  compact?: boolean;
}

const parseDistanceKm = (distance?: string): number | null => {
  if (!distance) return null;
  const match = distance.match(/([\d.]+)\s*(km|m)\b/i);
  if (!match) return null;
  const value = Number(match[1]);
  if (Number.isNaN(value)) return null;
  return match[2].toLowerCase() === "m" ? value / 1000 : value;
};

export const shouldShowLocalTransportBooking = (mode?: string, distance?: string): boolean => {
  const normalizedMode = (mode || "").toLowerCase();
  const distanceKm = parseDistanceKm(distance);
  if (normalizedMode.includes("walk") && (distanceKm === null || distanceKm <= 0.8)) return false;
  if (distanceKm !== null && distanceKm <= 0.8) return false;
  return Boolean(mode || distance);
};

const openTransportLink = (provider: "cab" | "auto" | "bike" | "bus", destination?: string) => {
  const encodedDestination = encodeURIComponent(destination || "");
  const urls = {
    cab: encodedDestination
      ? `https://m.uber.com/ul/?action=setPickup&dropoff[formatted_address]=${encodedDestination}`
      : "https://m.uber.com/",
    auto: "https://www.olacabs.com/",
    bike: "https://www.rapido.bike/",
    bus: encodedDestination
      ? `https://www.google.com/maps/dir/?api=1&destination=${encodedDestination}&travelmode=transit`
      : "https://www.google.com/maps/",
  };
  window.open(urls[provider], "_blank", "noopener,noreferrer");
};

export const LocalTransportBookingCard: React.FC<LocalTransportBookingCardProps> = ({
  mode,
  duration,
  distance,
  destination,
  compact = false,
}) => {
  if (!shouldShowLocalTransportBooking(mode, distance)) return null;

  const normalizedMode = (mode || "").toLowerCase();
  const isBus = normalizedMode.includes("bus");
  const isBike = normalizedMode.includes("bike") || normalizedMode.includes("scooter");
  const isAuto = normalizedMode.includes("auto") || normalizedMode.includes("rickshaw");
  const primaryLabel = isBus ? "View Bus Route" : isBike ? "Book Bike" : isAuto ? "Book Auto" : "Book Cab";
  const primaryProvider = isBus ? "bus" : isBike ? "bike" : isAuto ? "auto" : "cab";

  return (
    <div className={`my-2 rounded-xl border border-slate-200 bg-slate-50/80 text-left shadow-sm dark:border-slate-800 dark:bg-slate-900/50 ${compact ? "p-2.5" : "p-3"}`}>
      <div className="flex items-start gap-2.5">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-600 dark:bg-teal-950/30 dark:text-teal-300">
          {isBus ? <Bus className="h-4 w-4" /> : isBike ? <Bike className="h-4 w-4" /> : <Car className="h-4 w-4" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-extrabold uppercase tracking-wide text-slate-700 dark:text-slate-200">
              Travel
            </span>
            <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400">
              {[duration, distance].filter(Boolean).join(" • ")}
            </span>
          </div>
          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Book local transport before the next stop.
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => openTransportLink(primaryProvider, destination)}
              className="inline-flex items-center gap-1 rounded-lg bg-teal-600 px-2.5 py-1 text-[10px] font-extrabold text-white shadow-sm transition hover:bg-teal-700"
            >
              <Navigation className="h-3 w-3" />
              {primaryLabel}
            </button>
            {!isBus && (
              <>
                <button type="button" onClick={() => openTransportLink("cab", destination)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold text-slate-650 transition hover:border-teal-200 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300">
                  Cab
                </button>
                <button type="button" onClick={() => openTransportLink("auto", destination)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold text-slate-650 transition hover:border-teal-200 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300">
                  Auto
                </button>
                <button type="button" onClick={() => openTransportLink("bike", destination)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold text-slate-650 transition hover:border-teal-200 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300">
                  Bike
                </button>
              </>
            )}
            <ExternalLink className="mt-1 h-3.5 w-3.5 text-slate-350" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LocalTransportBookingCard;
