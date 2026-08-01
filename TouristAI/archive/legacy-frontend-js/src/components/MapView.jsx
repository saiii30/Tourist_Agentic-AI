import React from "react";
import { Marker, Popup } from "react-leaflet";
import L from "leaflet";

// Simple emoji icons for categories (can be replaced with custom images)
const categoryIcons = {
  restaurant: L.divIcon({ html: "🍽", className: "" }),
  hotel: L.divIcon({ html: "🏨", className: "" }),
  attraction: L.divIcon({ html: "🌟", className: "" }),
  museum: L.divIcon({ html: "🏛", className: "" }),
  park: L.divIcon({ html: "🌳", className: "" }),
  cafe: L.divIcon({ html: "☕", className: "" }),
  shopping: L.divIcon({ html: "🛍", className: "" }),
  hospital: L.divIcon({ html: "🏥", className: "" }),
  fuel: L.divIcon({ html: "⛽", className: "" }),
};

export default function MapView({ pois, onShowRoute, addPoi }) {
  return (
    <>
      {pois.map((p) => (
        <Marker
          key={p.id}
          position={[p.lat, p.lon]}
          icon={categoryIcons[p.tags?.amenity] || categoryIcons["attraction"]}
        >
          <Popup>
            <strong>{p.tags?.name || "Unnamed POI"}</strong>
            <br />
            {/* Simple details – more can be added later */}
            {Object.entries(p.tags || {})
              .filter(([k]) => k !== "name")
              .map(([k, v]) => (
                <span key={k}>
                  {k}: {v}
                  <br />
                </span>
              ))}
            <button onClick={() => onShowRoute(p)} className="route-btn">
              Show Route
            </button>
            {addPoi && (
              <button onClick={() => addPoi(p)} className="itinerary-btn">
                Add to Itinerary
              </button>
            )}
          </Popup>
        </Marker>
      ))}
    </>
  );
}
