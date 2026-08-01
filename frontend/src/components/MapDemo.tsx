// src/components/MapDemo.tsx
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

// Helper component to fit map bounds
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

export default function MapDemo() {
  // Hard‑coded itinerary example matching the required JSON shape
  const itinerary = {
    origin: { lat: 9.9697, lng: 77.4768 },
    destination: { lat: 12.4244, lng: 75.7382 },
    route: [
      [9.9697, 77.4768],
      [10.5, 77.0],
      [11.2, 76.4],
      [12.4244, 75.7382],
    ],
    hotels: [{ name: 'Coorg Resort', lat: 12.0, lng: 75.8 }],
    restaurants: [{ name: 'Spice Garden', lat: 11.5, lng: 76.0 }],
    attractions: [{ name: 'Abbey Falls', lat: 12.25, lng: 75.9 }],
  };

  const points = [...itinerary.route];

  return (
    <div className="max-w-4xl mx-auto p-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold mb-4 text-primary-600">
        Map Demo – Coorg 3‑Day Trip
      </h2>

      <MapContainer
        style={{ height: '500px', width: '100%' }}
        zoom={7}
        scrollWheelZoom={true}
        className="rounded-md"
      >
        {/* Light / Dark tile layer */}
        <TileLayer
          attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
          url={
            document.documentElement.classList.contains('dark')
              ? 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
              : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
          }
        />

        {/* Origin & Destination markers */}
        <Marker position={[itinerary.origin.lat, itinerary.origin.lng]} />
        <Marker position={[itinerary.destination.lat, itinerary.destination.lng]} />

        {/* Activity markers */}
        {itinerary.hotels.map((h, i) => (
          <Marker key={i} position={[h.lat, h.lng]} />
        ))}
        {itinerary.restaurants.map((r, i) => (
          <Marker key={i} position={[r.lat, r.lng]} />
        ))}
        {itinerary.attractions.map((a, i) => (
          <Marker key={i} position={[a.lat, a.lng]} />
        ))}

        {/* Route polyline with simple dash animation */}
        <Polyline
          positions={itinerary.route}
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
