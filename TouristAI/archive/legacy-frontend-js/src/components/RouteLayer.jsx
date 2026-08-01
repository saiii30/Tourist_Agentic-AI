import React from "react";
import { Polyline, Marker } from "react-leaflet";
import L from "leaflet";

const startIcon = L.divIcon({
  html: "<div style='background:green;width:12px;height:12px;border-radius:50%;'></div>",
  className: "",
  iconSize: [12, 12],
});
const endIcon = L.divIcon({
  html: "<div style='background:red;width:12px;height:12px;border-radius:50%;'></div>",
  className: "",
  iconSize: [12, 12],
});

export default function RouteLayer({ routeInfo }) {
  if (!routeInfo?.geometry) return null;
  const positions = routeInfo.geometry.map((c) => [c[1], c[0]]); // [lat, lng]
  const start = positions[0];
  const end = positions[positions.length - 1];
  return (
    <>
      <Polyline positions={positions} pathOptions={{ color: "#0066FF", weight: 6, lineCap: "round" }} />
      <Marker position={start} icon={startIcon} />
      <Marker position={end} icon={endIcon} />
    </>
  );
}
