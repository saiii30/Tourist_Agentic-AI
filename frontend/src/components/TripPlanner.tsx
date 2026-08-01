// src/components/TripPlanner.tsx
import { useState, useEffect } from 'react';
import { submitTrip } from '../api/trip';
import LoadingOverlay from './LoadingOverlay';
import MapWrapper from './MapWrapper';

export interface TripFormData {
  origin: string; // auto‑filled via geolocation when possible
  destination: string;
  start_date: string;
  // end_date is optional – we derive number of days from duration_days or calculate it
  end_date: string;
  travelers: number;
  budget_usd: number;
  interests: string[];
  transport: string;
  food_pref: string[];
  accommodation_type: string;
  free_text: string;
  // New fields for smart itinerary generation
  duration_days?: number; // number of days for the trip
  budget_target?: string; // Low | Moderate | High
  travel_style?: string; // e.g., Cultural & Historic, Adventure, Relaxation, Luxury
}

const initialForm: TripFormData = {
  origin: '',
  destination: '',
  start_date: '',
  end_date: '',
  travelers: 1,
  budget_usd: 0,
  interests: [],
  transport: 'flight',
  food_pref: [],
  accommodation_type: 'hotel',
  free_text: '',
  duration_days: 0,
  budget_target: '',
  travel_style: '',
};

export default function TripPlanner() {
  const [form, setForm] = useState<TripFormData>(initialForm);
  const [loading, setLoading] = useState(false);
  const [tripId, setTripId] = useState<string | null>(null);
  const [itinerary, setItinerary] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'plan' | 'map'>('plan');
  const [originDetected, setOriginDetected] = useState<boolean>(false);

  // ---------------------------------------------------------------------
  // Geolocation – prompt on component mount
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!navigator.geolocation) {
      console.warn('Geolocation not supported in this browser');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const resp = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`
          );
          const data = await resp.json();
          const city =
            data.address?.city ||
            data.address?.town ||
            data.address?.village ||
            data.display_name ||
            '';
          if (city) {
            setForm((prev) => ({ ...prev, origin: city }));
            setOriginDetected(true);
          }
        } catch (e) {
          console.error('Reverse geocoding failed', e);
        }
      },
      (error) => {
        console.warn('Geolocation permission denied or error', error);
        // No fallback needed – user can fill manually
      }
    );
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // If duration_days is not set, compute it from dates (inclusive)
    // Compute end_date if duration_days is provided
    if (form.start_date && form.duration_days) {
      const start = new Date(form.start_date);
      const end = new Date(start.getTime() + (form.duration_days - 1) * 24 * 60 * 60 * 1000);
      const iso = end.toISOString().split('T')[0];
      setForm((prev) => ({ ...prev, end_date: iso }));
    }
    const res = await submitTrip(form);
    setTripId(res.trip_id);
    setLoading(false);
  };

  // ---------------------------------------------------------------------
  // Fetch itinerary once we have a tripId
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!tripId) return;
    const fetchItinerary = async () => {
      try {
        const resp = await fetch(`/api/trip/${tripId}`);
        const data = await resp.json();
        setItinerary(data.data.itinerary);
      } catch (err) {
        console.error('Failed to load itinerary', err);
      }
    };
    fetchItinerary();
  }, [tripId]);

  return (
    <section className="max-w-5xl mx-auto p-6 bg-white/90 backdrop-blur-md rounded-xl shadow-lg">
      <h1 className="text-4xl font-extrabold text-primary-600 mb-4 text-center">
        AI Itinerary Generator
      </h1>
      <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5 mb-4">
        Current Place, Destination City, Start Date, Itinerary Duration (Days), Budget Target, Travel Style, Travel Mode (Transport Agent)
      </h3>

      {/* Tab navigation */}
      <div className="flex border-b mb-6 justify-center space-x-4">
        <button
          className={`px-5 py-2 ${activeTab === 'plan' ? 'border-b-2 border-primary-600 text-primary-600' : ''}`}
          onClick={() => setActiveTab('plan')}
        >
          Plan
        </button>
        {tripId && (
          <button
            className={`px-5 py-2 ${activeTab === 'map' ? 'border-b-2 border-primary-600 text-primary-600' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            Map
          </button>
        )}
      </div>

      {/* Form – shown when 'plan' tab active */}
      {activeTab === 'plan' && (
        <form className="space-y-6" onSubmit={handleSubmit}>
          {/* Origin – auto‑filled */}
            <div className="relative border-2 border-pink-500 p-2 rounded">
              <label className="block text-sm font-medium mb-1">Current Location</label>
              <input
                placeholder="Current Place (auto-detected)…"
                className="w-full px-4 py-2 rounded-xl bg-white/80 border border-gray-300 focus:border-primary-600 focus:ring-2 focus:ring-primary-200 shadow-sm"
                value={form.origin}
                onChange={(e) => setForm({ ...form, origin: e.target.value })}
                required
              />
              {originDetected && (
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-green-600">
                  📍 Detected
                </span>
              )}
            </div>

          {/* Destination */}
          <label className="block text-sm font-medium mb-1">Destination</label>
          <input
            placeholder="To (city, airport)…"
            className="input-primary w-full"
            value={form.destination}
            onChange={(e) => setForm({ ...form, destination: e.target.value })}
            required
          />

          {/* Dates */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block text-sm font-medium mb-1">Start Date</label>
            <input
              type="date"
              placeholder="Start Date"
              className="input-primary w-full"
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              required
            />
            <input
              type="number"
              min={1}
              placeholder="Itinerary Duration (Days)"
              className="input-primary w-full"
              value={form.duration_days ?? ''}
              onChange={(e) => setForm({ ...form, duration_days: Number(e.target.value) })}
              required
            />
          </div>

          {/* Travelers & Budget */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="number"
              min={1}
              placeholder="Travelers"
              className="input-primary w-full"
              value={form.travelers}
              onChange={(e) => setForm({ ...form, travelers: Number(e.target.value) })}
              required
            />
            <input
              type="number"
              min={0}
              placeholder="Budget (USD)"
              className="input-primary w-full"
              value={form.budget_usd}
              onChange={(e) => setForm({ ...form, budget_usd: Number(e.target.value) })}
              required
            />
          </div>

          {/* Budget Target */}
          <select
            className="input-primary w-full"
            value={form.budget_target}
            onChange={(e) => setForm({ ...form, budget_target: e.target.value })}
          >
            <option value="">Select Budget Target</option>
            <option value="Low">Low</option>
            <option value="Moderate">Moderate</option>
            <option value="High">High</option>
          </select>

          {/* Travel Style */}
          <select
            className="input-primary w-full"
            value={form.travel_style}
            onChange={(e) => setForm({ ...form, travel_style: e.target.value })}
          >
            <option value="">Select Travel Style</option>
            <option value="Cultural & Historic">Cultural & Historic</option>
            <option value="Adventure">Adventure</option>
            <option value="Relaxation">Relaxation</option>
            <option value="Luxury">Luxury</option>
          </select>

          {/* Travel Mode for Transport Agent */}
          <select
            className="input-primary w-full"
            value={form.transport}
            onChange={(e) => setForm({ ...form, transport: e.target.value })}
          >
            <option value="">Select Travel Mode (Access Transport Agent)</option>
            <option value="flight">Flight (Air)</option>
            <option value="train">Train (Rail)</option>
            <option value="bus">Bus (Intercity)</option>
            <option value="cab">Cab / Car Drive</option>
            <option value="all">All Transport Modes</option>
          </select>

          {/* Interests */}
          <textarea
            placeholder="Interests (comma separated)…"
            className="border rounded px-3 py-2 w-full h-24 focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={form.interests.join(', ')}
            onChange={(e) =>
              setForm({ ...form, interests: e.target.value.split(',').map((s) => s.trim()) })
            }
          />

          {/* Free description */}
          <textarea
            placeholder="Free description – e.g. \"I want a romantic dinner on day 2, love night markets\""
            className="border rounded px-3 py-2 w-full h-32 focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={form.free_text}
            onChange={(e) => setForm({ ...form, free_text: e.target.value })}
          />

          <button
            type="submit"
            className="w-full md:w-auto bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold px-6 py-2 rounded-xl shadow-md hover:opacity-90 transition"
            disabled={loading}
          >
            {loading ? 'Planning…' : 'Generate Itinerary'}
          </button>
        </form>
      )}

      {/* Map tab */}
      {activeTab === 'map' && itinerary && (
        <MapWrapper
          origin={itinerary.origin}
          destination={itinerary.destination}
          route={itinerary.route}
          hotels={itinerary.hotels}
          restaurants={itinerary.restaurants}
          attractions={itinerary.attractions}
        />
      )}

      {/* Loading overlay */}
      {loading && tripId && <LoadingOverlay tripId={tripId} />}

      {/* Direct itinerary display when loaded */}
      {itinerary && activeTab === 'plan' && (
        <div className="mt-8 p-4 bg-gray-50 rounded-lg shadow-inner">
          <h2 className="text-2xl font-bold mb-4">Your Itinerary</h2>
          <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(itinerary, null, 2)}</pre>
        </div>
      )}
    </section>
  );
}
