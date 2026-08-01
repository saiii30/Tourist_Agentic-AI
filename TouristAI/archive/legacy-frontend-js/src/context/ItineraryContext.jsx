import React, { createContext, useState } from "react";

// Basic Itinerary context for the map and other agents
export const ItineraryContext = createContext({
  itinerary: [],
  addPoi: () => {},
  updateItinerary: () => {},
});

export const ItineraryProvider = ({ children }) => {
  const [itinerary, setItinerary] = useState([]);

  // Add a POI to the itinerary for the current day (default day 1)
  const addPoi = (poi, day = 1) => {
    setItinerary((prev) => {
      const dayItems = prev.filter((i) => i.day === day);
      const order = dayItems.length + 1;
      const newItem = {
        id: poi.id,
        name: poi.tags?.name || "Unnamed POI",
        lat: poi.lat,
        lng: poi.lon,
        category: poi.tags?.amenity || "attraction",
        day,
        order,
        // optional extra fields
        rating: Number(poi.tags?.rating) || null,
        price: poi.tags?.price || null,
      };
      return [...prev, newItem];
    });
  };

  const updateItinerary = (newItinerary) => {
    setItinerary(newItinerary);
  };

  return (
    <ItineraryContext.Provider value={{ itinerary, addPoi, updateItinerary }}>
      {children}
    </ItineraryContext.Provider>
  );
};
