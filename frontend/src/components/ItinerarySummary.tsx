// src/components/ItinerarySummary.tsx
import React from 'react';

interface ItinerarySummaryProps {
  itinerary: any; // shape depends on backend response
}

const ItinerarySummary: React.FC<ItinerarySummaryProps> = ({ itinerary }) => {
  const destination = itinerary.destination || 'Unknown';
  const budget = itinerary.budget_usd ? `$${itinerary.budget_usd}` : 'N/A';
  const travelers = itinerary.travelers || 1;
  const interests = itinerary.interests?.join(', ') || 'None';
  const attractionsCount = itinerary.attractions?.length || 0;
  const restaurantsCount = itinerary.restaurants?.length || 0;
  const hotelsCount = itinerary.hotels?.length || 0;
  const distance = itinerary.distance_km ? `${itinerary.distance_km} km` : 'N/A';
  const estBudget = itinerary.estimated_budget?.toLocaleString() ? `₹${itinerary.estimated_budget?.toLocaleString()}` : 'N/A';
  const activeHours = itinerary.active_hours || `${itinerary.duration_days || 1} Days`;
  const forecast = itinerary.forecast?.temp || '—';

  return (
    <div className="mt-8 p-6 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg space-y-4">
      <h2 className="text-2xl font-bold text-primary-600 mb-4">Itinerary Summary</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div><strong>Destination:</strong> {destination}</div>
        <div><strong>Budget Target:</strong> {budget}</div>
        <div><strong>Travelers:</strong> {travelers}</div>
        <div><strong>Interests:</strong> {interests}</div>
        <div><strong>Rating:</strong> ⭐ 4.5</div>
        <div><strong>Attractions:</strong> 📍 {attractionsCount} Places</div>
        <div><strong>Restaurants:</strong> 🍽 {restaurantsCount} Dinings</div>
        <div><strong>Hotels:</strong> 🏨 {hotelsCount} Stays</div>
        <div><strong>Distance:</strong> 🚗 {distance}</div>
        <div><strong>Est Budget:</strong> 💰 {estBudget}</div>
        <div><strong>Active hours:</strong> ⏱ {activeHours}</div>
        <div><strong>Forecast:</strong> 🌤 {forecast}°C</div>
      </div>
    </div>
  );
};

export default ItinerarySummary;
