import { useEffect, useMemo, useState } from "react";
import axios from "axios";

type Place = {
  name: string;
  city: string;
  lat: number;
  lon: number;
  history: string;
};

function haversine(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
) {
  const R = 6371;

  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) *
      Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  return 2 * R * Math.asin(Math.sqrt(a));
}

function bearing(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
) {
  const toRad = (x: number) => (x * Math.PI) / 180;

  const y =
    Math.sin(toRad(lon2 - lon1)) *
    Math.cos(toRad(lat2));

  const x =
    Math.cos(toRad(lat1)) *
      Math.sin(toRad(lat2)) -
    Math.sin(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.cos(toRad(lon2 - lon1));

  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

export default function NearbyExplorer() {
  const [coords, setCoords] = useState<any>(null);

  const [places, setPlaces] = useState<Place[]>([]);

  const [heading, setHeading] = useState(0);

  const [demoMode, setDemoMode] = useState(true);

  const cities = [
    {
      city: "Delhi",
      lat: 28.6139,
      lon: 77.209,
    },
    {
      city: "Jaipur",
      lat: 26.9124,
      lon: 75.7873,
    },
    {
      city: "Goa",
      lat: 15.2993,
      lon: 74.124,
    },
    {
      city: "Madurai",
      lat: 9.9252,
      lon: 78.1198,
    },
    {
      city: "Chennai",
      lat: 13.0827,
      lon: 80.2707,
    },
  ];

  useEffect(() => {
    if (!demoMode) {
      navigator.geolocation.getCurrentPosition((p) => {
        setCoords({
          lat: p.coords.latitude,
          lon: p.coords.longitude,
        });
      });
    }
  }, [demoMode]);

  useEffect(() => {
    if (!coords) return;

    axios
      .get("/api/nearby", {
        params: coords,
      })
      .then((r) => setPlaces(r.data))
      .catch(console.error);
  }, [coords]);

  useEffect(() => {
    if (demoMode) return;

    const handler = (e: any) => {
      if (e.alpha != null)
        setHeading((360 - e.alpha) % 360);
    };

    window.addEventListener(
      "deviceorientation",
      handler
    );

    return () =>
      window.removeEventListener(
        "deviceorientation",
        handler
      );
  }, [demoMode]);

  const visible = useMemo(() => {
    if (!coords) return [];

    return places
      .map((p) => {
        const b = bearing(
          coords.lat,
          coords.lon,
          p.lat,
          p.lon
        );

        const d = Math.abs(
          ((((b - heading) % 360) + 540) % 360) -
            180
        );

        return {
          ...p,
          distance: haversine(
            coords.lat,
            coords.lon,
            p.lat,
            p.lon
          ),
          delta: d,
        };
      })
      .filter((x) => x.delta < 45)
      .sort((a, b) => a.distance - b.distance);
  }, [places, heading, coords]);

  const speak = (txt: string) => {
    speechSynthesis.cancel();

    speechSynthesis.speak(
      new SpeechSynthesisUtterance(txt)
    );
  };

  return (
  <div className="h-full p-4 bg-gray-50">

    {/* Header */}
    <div className="flex items-center justify-between mb-5">

      <h2 className="text-lg font-semibold">
        🧭 Nearby Explorer
      </h2>

      <label className="flex items-center gap-2 text-sm">

        Demo Mode

        <input
          type="checkbox"
          checked={demoMode}
          onChange={() => setDemoMode(!demoMode)}
        />

      </label>

    </div>

    {/* Demo Controls */}
    {demoMode && (
      <div className="bg-white border rounded-xl p-4 mb-5 shadow-sm">

        <label className="block text-sm font-medium mb-2">
          Select Demo City
        </label>

        <select
          className="w-full border rounded-lg p-2 mb-4"
          onChange={(e) => {
            const c = cities.find(
              (x) => x.city === e.target.value
            );

            if (c) setCoords(c);
          }}
        >
          <option>Select City</option>

          {cities.map((c) => (
            <option key={c.city}>{c.city}</option>
          ))}
        </select>

        <label className="text-sm font-medium">
          Demo Compass
        </label>

        <input
          type="range"
          min={0}
          max={360}
          value={heading}
          onChange={(e) =>
            setHeading(Number(e.target.value))
          }
          className="w-full mt-2"
        />

        <div className="text-center mt-2 text-lg font-semibold text-blue-600">
          {heading}°
        </div>

      </div>
    )}

    {!coords && (
      <div className="text-sm text-gray-500 text-center py-10">
        Select a demo city to begin.
      </div>
    )}

    {/* Nearby Places */}
    <div className="space-y-4">

      {visible.map((p) => (
        <div
          key={p.name}
          className="bg-white rounded-xl border p-4 shadow-sm"
        >

          <div className="flex justify-between">

            <div>

              <h3 className="font-semibold">
                {p.name}
              </h3>

              <p className="text-xs text-gray-500">
                {p.city}
              </p>

            </div>

            <div className="text-right text-xs text-gray-500">

              <div>
                {p.distance.toFixed(2)} km
              </div>

              <div>
                {Math.round(p.delta)}°
              </div>

            </div>

          </div>

          <p className="mt-3 text-sm text-gray-700">
            {p.history.length > 180
              ? p.history.slice(0, 180) + "..."
              : p.history}
          </p>

          <div className="flex gap-2 mt-4">

            <button
            //   onClick={() => speak(p.history)}
            onClick={() =>
    speak(
        `Hi User..Welcome to ${p.name}. This is one of the famous tourist attractions in ${p.city}.`
    )
}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm hover:bg-blue-700"
            >
              🔊 Whisper
            </button>

            <a
              href={`https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lon}`}
              target="_blank"
              rel="noreferrer"
              className="flex-1 bg-green-600 text-white rounded-lg py-2 text-center text-sm hover:bg-green-700"
            >
              Directions
            </a>

          </div>

        </div>
      ))}

    </div>

  </div>
);}