import React, { useState, useEffect, useRef } from "react";
import {
  Compass, Hospital, ShoppingBag, PhoneCall,
  MapPin, ExternalLink, ShieldAlert, Navigation, Crosshair, ZoomIn, ZoomOut, RefreshCw
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { apiUrl } from "../../api/config";

interface EmergencyContact {
  role: string;
  number: string;
  location: string;
}

interface NearbyExplorerWidgetProps {
  cityName: string;
  emergencyContacts?: EmergencyContact[];
}

interface NearbyPlace {
  id: string;
  name: string;
  category: "hospital" | "pharmacy" | "clinic" | "shop" | "emergency" | "landmark";
  categoryLabel: string;
  address: string;
  phone?: string;
  distance: string;
  lat: number;
  lng: number;
  details: string;
}

const CITY_COORDS: Record<string, { lat: number; lng: number }> = {
  madurai: { lat: 9.9252, lng: 78.1198 },
  chennai: { lat: 13.0827, lng: 80.2707 },
  bangalore: { lat: 12.9716, lng: 77.5946 },
  bengaluru: { lat: 12.9716, lng: 77.5946 },
  coimbatore: { lat: 11.0168, lng: 76.9558 },
  delhi: { lat: 28.6139, lng: 77.2090 },
  mumbai: { lat: 19.0760, lng: 72.8777 },
  hyderabad: { lat: 17.3850, lng: 78.4867 },
  kochi: { lat: 9.9312, lng: 76.2673 },
  kerala: { lat: 10.8505, lng: 76.2711 },
  goa: { lat: 15.2993, lng: 74.1240 },
  ooty: { lat: 11.4102, lng: 76.6950 },
  kodaikanal: { lat: 10.2381, lng: 77.4892 },
  jaipur: { lat: 26.9124, lng: 75.7873 },
  agra: { lat: 27.1767, lng: 78.0081 },
  varanasi: { lat: 25.3176, lng: 82.9739 },
};

const normalizeCategory = (category: string, label?: string): NearbyPlace["category"] => {
  const value = `${category || ""} ${label || ""}`.toLowerCase();
  if (value.includes("pharmacy")) return "pharmacy";
  if (value.includes("clinic") || value.includes("doctor")) return "clinic";
  if (value.includes("hospital")) return "hospital";
  if (value.includes("police") || value.includes("fire") || value.includes("emergency")) return "emergency";
  if (value.includes("shop") || value.includes("supermarket") || value.includes("mall") || value.includes("atm") || value.includes("fuel")) return "shop";
  return "landmark";
};

const labelForNearbyCategory = (category: NearbyPlace["category"]) => {
  if (category === "hospital") return "Hospital & ER";
  if (category === "pharmacy") return "Pharmacy";
  if (category === "clinic") return "Clinic / Doctor";
  if (category === "shop") return "Shop / Essentials";
  if (category === "emergency") return "Emergency";
  return "Key Place";
};

export const NearbyExplorerWidget: React.FC<NearbyExplorerWidgetProps> = ({
  cityName,
  emergencyContacts = [],
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const [showEmergencyQuickCall, setShowEmergencyQuickCall] = useState<boolean>(false);
  const [leafletLoaded, setLeafletLoaded] = useState<boolean>(false);
  const [userGps, setUserGps] = useState<{ lat: number; lng: number } | null>(null);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [livePlaces, setLivePlaces] = useState<NearbyPlace[]>([]);
  const [nearbyLoading, setNearbyLoading] = useState<boolean>(false);
  const [nearbyError, setNearbyError] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<"nearest" | "priority">("nearest");

  const normCity = (cityName || "Madurai").trim();
  const baseCoords = CITY_COORDS[normCity.toLowerCase()] || { lat: 9.9252, lng: 78.1198 };

  // 1. Ensure Leaflet JS & CSS are loaded even if the main Map tab was never opened.
  useEffect(() => {
    const L = (window as any).L;
    if (L) {
      setLeafletLoaded(true);
      return;
    }

    if (!document.getElementById("leaflet-css-cdn")) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      link.id = "leaflet-css-cdn";
      document.head.appendChild(link);
    }

    if (!document.getElementById("leaflet-js-cdn")) {
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.id = "leaflet-js-cdn";
      script.async = true;
      script.onload = () => setLeafletLoaded(true);
      document.body.appendChild(script);
    }

    const checkInterval = setInterval(() => {
      if ((window as any).L) {
        setLeafletLoaded(true);
        clearInterval(checkInterval);
      }
    }, 300);

    return () => clearInterval(checkInterval);
  }, []);

  const places: NearbyPlace[] = [...livePlaces];

  // Merge any dynamic emergency contacts provided
  emergencyContacts.forEach((contact, idx) => {
    if (!places.some(p => p.name.toLowerCase().includes(contact.role.toLowerCase()))) {
      places.push({
        id: `dyn-emg-${idx}`,
        name: contact.role,
        category: "emergency",
        categoryLabel: "Emergency Helpline",
        address: contact.location || `${normCity} Helpline`,
        phone: contact.number,
        distance: "Instant",
        lat: baseCoords.lat + 0.001 * (idx + 1),
        lng: baseCoords.lng + 0.001 * (idx + 1),
        details: "Toll-free emergency contact"
      });
    }
  });

  useEffect(() => {
    if (!navigator.geolocation || userGps) return;
    handleLocateUser();
  }, [userGps]);

  useEffect(() => {
    if (!userGps) return;

    const controller = new AbortController();
    const params = new URLSearchParams({
      lat: String(userGps.lat),
      lng: String(userGps.lng),
      radius: "5000",
    });
    ["hospital", "pharmacy", "clinic", "police", "fire_station", "shop", "atm", "fuel"].forEach((cat) => {
      params.append("category", cat);
    });

    setNearbyLoading(true);
    setNearbyError(null);
    fetch(apiUrl(`/api/nearby?${params.toString()}`), { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Nearby lookup failed (${res.status})`);
        return res.json();
      })
      .then((items) => {
        const next: NearbyPlace[] = (Array.isArray(items) ? items : []).slice(0, 40).map((item: any) => {
          const category = normalizeCategory(item.category, item.category_label);
          const distanceMeters = Number(item.distance_m || 0);
          return {
            id: String(item.id),
            name: item.name || item.category_label || "Nearby place",
            category,
            categoryLabel: item.category_label || labelForNearbyCategory(category),
            address: item.address || "Address not listed",
            phone: item.phone || undefined,
            distance: distanceMeters >= 1000 ? `${(distanceMeters / 1000).toFixed(1)} km` : `${Math.max(1, Math.round(distanceMeters))} m`,
            lat: Number(item.lat),
            lng: Number(item.lon),
            details: `${item.category_label || labelForNearbyCategory(category)} within 5 km of your live location`,
          };
        }).filter((item: NearbyPlace) => Number.isFinite(item.lat) && Number.isFinite(item.lng));
        setLivePlaces(next);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setNearbyError(err.message || "Could not load nearby places.");
          setLivePlaces([]);
        }
      })
      .finally(() => setNearbyLoading(false));

    return () => controller.abort();
  }, [userGps]);

  const getDistanceMeters = (distance: string) => {
    const value = parseFloat(distance || "0");
    if (!Number.isFinite(value)) return 999999;
    return distance.toLowerCase().includes("km") ? value * 1000 : value;
  };

  const getSafetyPriority = (place: NearbyPlace) => {
    const base = place.category === "hospital" ? 100 : place.category === "pharmacy" ? 90 : place.category === "clinic" ? 80 : place.category === "emergency" ? 75 : place.category === "shop" ? 45 : 30;
    const distancePenalty = Math.min(getDistanceMeters(place.distance) / 100, 35);
    const phoneBonus = place.phone ? 8 : 0;
    return base + phoneBonus - distancePenalty;
  };

  const filteredPlaces = (activeCategory === "all"
    ? places
    : places.filter(p => p.category === activeCategory)
  ).sort((a, b) => {
    if (sortMode === "priority") return getSafetyPriority(b) - getSafetyPriority(a);
    return getDistanceMeters(a.distance) - getDistanceMeters(b.distance);
  });

  // 3. Initialize & update Leaflet OpenStreetMap instance
  useEffect(() => {
    if (!leafletLoaded || !mapContainerRef.current) return;
    const L = (window as any).L;
    if (!L) return;

    // Destroy previous map instance cleanly
    if (mapInstanceRef.current) {
      try {
        mapInstanceRef.current.remove();
      } catch (e) {}
      mapInstanceRef.current = null;
    }

    try {
      const centerLat = userGps ? userGps.lat : baseCoords.lat;
      const centerLng = userGps ? userGps.lng : baseCoords.lng;

      const map = L.map(mapContainerRef.current, {
        scrollWheelZoom: true,
        zoomControl: false,
      }).setView([centerLat, centerLng], 14);

      mapInstanceRef.current = map;

      // Add high quality CartoDB Voyager map tiles
      L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: "abcd",
        maxZoom: 19,
      }).addTo(map);

      // Add Center User Marker
      const centerIcon = L.divIcon({
        className: "custom-center-marker",
        html: `
          <div style="
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #0d9488;
            border: 3px solid white;
            box-shadow: 0 0 12px rgba(13,148,136,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <div style="width: 6px; height: 6px; border-radius: 50%; background: white;"></div>
          </div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });

      L.marker([centerLat, centerLng], { icon: centerIcon })
        .addTo(map)
        .bindPopup(`<b>Your Location</b><br>${normCity}`);

      // Add Places Markers
      markersRef.current = [];
      filteredPlaces.forEach((place) => {
        let pinColor = "#0284c7"; // sky
        if (place.category === "hospital") pinColor = "#e11d48"; // rose
        if (place.category === "pharmacy") pinColor = "#10b981"; // emerald
        if (place.category === "clinic") pinColor = "#06b6d4"; // cyan
        if (place.category === "emergency") pinColor = "#dc2626"; // red
        if (place.category === "shop") pinColor = "#d97706"; // amber
        if (place.category === "landmark") pinColor = "#059669"; // emerald

        const placeIcon = L.divIcon({
          className: "custom-place-marker",
          html: `
            <div style="
              width: 16px;
              height: 16px;
              border-radius: 50%;
              background: ${pinColor};
              border: 2px solid white;
              box-shadow: 0 2px 6px rgba(0,0,0,0.4);
              cursor: pointer;
            "></div>
          `,
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });

        const popupContent = `
          <div style="font-family: sans-serif; font-size: 11px; text-align: left; padding: 2px;">
            <b style="color: #1e293b; font-size: 12px;">${place.name}</b><br/>
            <span style="color: #0d9488; font-weight: bold;">📍 ${place.distance} away</span><br/>
            <span style="color: #64748b;">${place.address}</span><br/>
            ${place.phone ? `<a href="tel:${place.phone.split('/')[0].trim()}" style="display:inline-block; margin-top:4px; padding:3px 8px; background:#0d9488; color:white; border-radius:4px; text-decoration:none; font-weight:bold;">📞 Call ${place.phone.split('/')[0].trim()}</a>` : ''}
          </div>
        `;

        const m = L.marker([place.lat, place.lng], { icon: placeIcon })
          .addTo(map)
          .bindPopup(popupContent);

        m.on("click", () => {
          setSelectedPlaceId(place.id);
        });

        markersRef.current.push({ id: place.id, marker: m, lat: place.lat, lng: place.lng });
      });

      setTimeout(() => {
        try {
          map.invalidateSize();
        } catch (e) {}
      }, 120);

    } catch (err) {
      console.error("Error initializing Leaflet map:", err);
    }
  }, [leafletLoaded, activeCategory, normCity, userGps]);

  // Handle flying to place on list item click
  const handleSelectPlace = (place: NearbyPlace) => {
    setSelectedPlaceId(place.id);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([place.lat, place.lng], 16, { animate: true, duration: 1.2 });
      const item = markersRef.current.find(m => m.id === place.id);
      if (item && item.marker) {
        item.marker.openPopup();
      }
    }
  };

  // Handle Browser Geolocation
  const handleLocateUser = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsLocating(false);
        const userCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserGps(userCoords);
        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo([userCoords.lat, userCoords.lng], 15, { animate: true });
        }
      },
      (err) => {
        setIsLocating(false);
        alert(`Could not get your location: ${err.message}. Using city center.`);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleZoomIn = () => {
    if (mapInstanceRef.current) mapInstanceRef.current.zoomIn();
  };

  const handleZoomOut = () => {
    if (mapInstanceRef.current) mapInstanceRef.current.zoomOut();
  };

  const handleRecenter = () => {
    if (mapInstanceRef.current) {
      const L = (window as any).L;
      if (L && markersRef.current.length > 0) {
        const points = markersRef.current.map((item) => [item.lat, item.lng]);
        if (userGps) points.push([userGps.lat, userGps.lng]);
        mapInstanceRef.current.fitBounds(L.latLngBounds(points), { padding: [24, 24], maxZoom: 15 });
        return;
      }
      const lat = userGps ? userGps.lat : baseCoords.lat;
      const lng = userGps ? userGps.lng : baseCoords.lng;
      mapInstanceRef.current.flyTo([lat, lng], 14, { animate: true });
    }
  };

  return (
    <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4 text-left">
      {/* Header with Compass Controls */}
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-teal-500/10 dark:bg-teal-400/10 flex items-center justify-center border border-teal-500/20">
            <Compass className="w-4 h-4 text-teal-600 dark:text-teal-400 animate-spin-slow" />
          </div>
          <div>
            <h4 className="font-heading text-xs font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              Live 5 km Safety Compass
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block" />
            </h4>
            <p className="text-[10px] text-slate-400 dark:text-slate-400">
              {userGps ? "Hospitals, pharmacies, shops and emergency places near your GPS" : "Allow GPS to find accurate nearby help within 5 km"}
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowEmergencyQuickCall(!showEmergencyQuickCall)}
          className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200/60 dark:border-rose-900/40 flex items-center gap-1 hover:bg-rose-100 dark:hover:bg-rose-900/50 transition-colors"
        >
          <PhoneCall className="w-3 h-3 text-rose-500 animate-pulse" />
          {showEmergencyQuickCall ? "Hide 112" : "112 Helplines"}
        </button>
      </div>

      {/* Quick Emergency Helplines Call Bar */}
      <AnimatePresence>
        {showEmergencyQuickCall && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 bg-rose-500/5 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/30 rounded-xl space-y-2 text-xs">
              <p className="font-bold text-rose-700 dark:text-rose-300 text-[11px] flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                Toll-Free National Emergency Contacts
              </p>
              <div className="grid grid-cols-3 gap-1.5">
                <a
                  href="tel:112"
                  className="p-1.5 bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/50 rounded-lg text-center font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 transition-colors"
                >
                  <div className="text-[10px] text-slate-400 font-normal">Emergency</div>
                  112
                </a>
                <a
                  href="tel:100"
                  className="p-1.5 bg-white dark:bg-slate-900 border border-sky-200 dark:border-sky-900/50 rounded-lg text-center font-bold text-sky-600 dark:text-sky-400 hover:bg-sky-50 transition-colors"
                >
                  <div className="text-[10px] text-slate-400 font-normal">Police</div>
                  100
                </a>
                <a
                  href="tel:108"
                  className="p-1.5 bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-900/50 rounded-lg text-center font-bold text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 transition-colors"
                >
                  <div className="text-[10px] text-slate-400 font-normal">Ambulance</div>
                  108
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* REAL LEAFLET OPENSTREETMAP CONTAINER WITH COMPASS OVERLAY */}
      <div className="relative w-full h-52 bg-slate-900 rounded-xl overflow-hidden border border-slate-700 shadow-md">
        {!leafletLoaded && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950 text-xs font-bold text-slate-300">
            Loading map compass...
          </div>
        )}
        <div ref={mapContainerRef} className="w-full h-full z-0" />

        {/* Real Compass Controls Overlay */}
        <div className="absolute top-2 right-2 z-10 flex flex-col gap-1 bg-slate-900/80 backdrop-blur-md p-1 rounded-lg border border-slate-700/80 shadow-lg">
          <button
            onClick={handleLocateUser}
            title="Locate My GPS Position"
            className="p-1.5 bg-teal-500/20 text-teal-300 rounded hover:bg-teal-500/40 transition-colors flex items-center justify-center"
          >
            <Crosshair className={`w-3.5 h-3.5 ${isLocating ? "animate-spin text-teal-400" : ""}`} />
          </button>
          <button
            onClick={handleRecenter}
            title="Recenter Compass Map"
            className="p-1.5 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition-colors flex items-center justify-center"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomIn}
            title="Zoom In"
            className="p-1.5 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition-colors flex items-center justify-center"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            title="Zoom Out"
            className="p-1.5 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition-colors flex items-center justify-center"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Compass Cardinal Badge Overlay */}
        <div className="absolute top-2 left-2 z-10 bg-slate-900/80 backdrop-blur-md px-2 py-1 rounded-lg border border-slate-700/80 flex items-center gap-1.5 shadow-md">
          <div className="w-4 h-4 rounded-full bg-teal-500/20 border border-teal-400 flex items-center justify-center">
            <span className="text-[8px] font-bold text-teal-400">N</span>
          </div>
          <span className="text-[10px] font-bold text-slate-200">
            {userGps ? "Live GPS · 5 km" : `${normCity} Preview`}
          </span>
        </div>
      </div>

      {nearbyError && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-[10.5px] font-semibold text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/25 dark:text-amber-300">
          {nearbyError}
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        {[
          { key: "all", label: "All Nearby", icon: Compass },
          { key: "hospital", label: "🏥 Hospitals", icon: Hospital },
          { key: "pharmacy", label: "💊 Pharmacy", icon: Hospital },
          { key: "clinic", label: "🩺 Clinic", icon: Hospital },
          { key: "shop", label: "🛍️ Shops", icon: ShoppingBag },
          { key: "emergency", label: "🚨 Emergency", icon: ShieldAlert },
        ].map((tab) => {
          const isActive = activeCategory === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveCategory(tab.key)}
              className={`px-2.5 py-1 rounded-xl text-[10.5px] font-bold whitespace-nowrap transition-all border ${
                isActive
                  ? "bg-teal-500 text-white border-teal-500 shadow-sm"
                  : "bg-slate-50 dark:bg-slate-900/60 text-slate-600 dark:text-slate-400 border-slate-200/60 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-850"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
        <label className="shrink-0 rounded-xl border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-bold text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
          <select value={sortMode} onChange={(event) => setSortMode(event.target.value as "nearest" | "priority")} className="bg-transparent outline-none">
            <option value="nearest">Nearest</option>
            <option value="priority">Emergency priority</option>
          </select>
        </label>
      </div>

      {/* Place List Cards */}
      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
        {nearbyLoading && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-center text-[11px] font-bold text-slate-500 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-400">
            Finding real nearby places within 5 km...
          </div>
        )}
        {!nearbyLoading && userGps && filteredPlaces.length === 0 && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-center text-[11px] font-bold text-slate-500 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-400">
            No matching places found within 5 km for this filter.
          </div>
        )}
        {filteredPlaces.map((place) => {
          const isSelected = place.id === selectedPlaceId;
          const isHospital = place.category === "hospital";
          const isPharmacy = place.category === "pharmacy";
          const isClinic = place.category === "clinic";
          const isShop = place.category === "shop";
          const isEmergency = place.category === "emergency";

          let categoryBadge = "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-400 dark:border-sky-900/50";
          if (isHospital) categoryBadge = "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/50";
          if (isPharmacy) categoryBadge = "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/50";
          if (isClinic) categoryBadge = "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/40 dark:text-cyan-400 dark:border-cyan-900/50";
          if (isShop) categoryBadge = "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/50";
          if (isEmergency) categoryBadge = "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/50";

          const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name + " " + place.address)}`;
          const priority = Math.round(getSafetyPriority(place));

          return (
            <div
              key={place.id}
              onClick={() => handleSelectPlace(place)}
              className={`p-2.5 border rounded-xl transition-all cursor-pointer text-xs space-y-1.5 ${
                isSelected
                  ? "border-teal-500 bg-teal-500/5 dark:bg-teal-950/30 ring-1 ring-teal-500/40"
                  : "border-slate-150 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/20 hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <span className={`inline-block text-[9.5px] font-bold px-2 py-0.5 rounded-full border mb-1 ${categoryBadge}`}>
                    {place.categoryLabel}
                  </span>
                  {sortMode === "priority" && (
                    <span className="ml-1 inline-block text-[9px] font-bold px-2 py-0.5 rounded-full border border-teal-200 bg-teal-50 text-teal-700 dark:border-teal-900/50 dark:bg-teal-950/40 dark:text-teal-300">
                      Priority {priority}
                    </span>
                  )}
                  <h5 className="font-bold text-slate-800 dark:text-slate-200 text-xs truncate leading-snug">
                    {place.name}
                  </h5>
                </div>
                <span className="text-[10px] font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50 px-2 py-0.5 rounded-full shrink-0 border border-teal-200/50 dark:border-teal-900/40">
                  📍 {place.distance}
                </span>
              </div>

              <p className="text-[10.5px] text-slate-500 dark:text-slate-400 line-clamp-1 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                {place.address}
              </p>

              <p className="text-[10px] text-slate-400 dark:text-slate-500 italic">
                {place.details}
              </p>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-1 border-t border-slate-100 dark:border-slate-800/80">
                {place.phone && (
                  <a
                    href={`tel:${place.phone.split("/")[0].trim()}`}
                    onClick={(e) => e.stopPropagation()}
                    className="flex-1 py-1 px-2 rounded-lg bg-teal-500/10 text-teal-700 dark:text-teal-300 text-[10px] font-bold flex items-center justify-center gap-1 hover:bg-teal-500/20 transition-colors"
                  >
                    <PhoneCall className="w-3 h-3" />
                    Call ({place.phone.split("/")[0].trim()})
                  </a>
                )}
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="flex-1 py-1 px-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-bold flex items-center justify-center gap-1 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                  <Navigation className="w-3 h-3 text-teal-500" />
                  Map Compass
                  <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NearbyExplorerWidget;
