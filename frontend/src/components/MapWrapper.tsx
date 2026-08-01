// src/components/MapWrapper.tsx
import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { motion } from 'framer-motion';
import L from 'leaflet';

// Fix default icon URLs for Vite bundling
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Helper to fit map bounds to points
const FitBounds = ({ points }: { points: [number, number][] }) => {
  const map = useMap();
  React.useEffect(() => {
    if (points.length) {
      const bounds = L.latLngBounds(points.map(p => L.latLng(p[0], p[1])));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, points]);
  return null;
};

/**
 * Props expect the same structure as the itinerary JSON described in the requirements.
 */
export interface ItineraryProps {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  route: [number, number][];
  hotels?: { name: string; lat: number; lng: number }[];
  restaurants?: { name: string; lat: number; lng: number }[];
  attractions?: { name: string; lat: number; lng: number }[];
}

export default function MapWrapper({ origin, destination, route, hotels = [], restaurants = [], attractions = [] }: ItineraryProps) {
  const points = [...route];

  return (
    <div className="w-full h-full max-w-4xl mx-auto p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <MapContainer
        style={{ height: '500px', width: '100%' }}
        zoom={7}
        scrollWheelZoom={true}
        className="rounded-md"
      >
        {/* Light / Dark OSM tiles */}
        <TileLayer
          attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
          url={
            document.documentElement.classList.contains('dark')
              ? 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
              : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
          }
        />

        {/* Origin & destination markers */}
        <Marker position={[origin.lat, origin.lng]} />
        <Marker position={[destination.lat, destination.lng]} />

        {/* Activity markers */}
        {hotels.map((h, i) => (
          <Marker key={i} position={[h.lat, h.lng]} />
        ))}
        {restaurants.map((r, i) => (
          <Marker key={i} position={[r.lat, r.lng]} />
        ))}
        {attractions.map((a, i) => (
          <Marker key={i} position={[a.lat, a.lng]} />
        ))}

        {/* Animated route polyline */}
        <Polyline
          positions={route}
          color="#2563EB"
          weight={4}
          opacity={0.8}
          pathOptions={{ dashArray: '10 10' }}
        >
          <motion.path
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatType: 'reverse' }}
          />
        </Polyline>

        {/* Auto‑fit bounds */}
        <FitBounds points={points} />
      </MapContainer>
    </div>
  );
}
