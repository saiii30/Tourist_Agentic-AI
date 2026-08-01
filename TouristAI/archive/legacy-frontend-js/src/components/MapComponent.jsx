import React, { useState, useEffect, useCallback, useContext } from "react";
import { MapContainer, TileLayer, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "../styles/map.css";
import FilterPanel from "./FilterPanel";
import DayTabs from "./DayTabs";
import MapView from "./MapView";
import LoadingOverlay from "./LoadingOverlay";
import { ItineraryContext } from "../../context/ItineraryContext";

export default function MapComponent() {
  const [center, setCenter] = useState({ lat: 48.8584, lng: 2.2945 }); // default Paris
  const [categoryFilters, setCategoryFilters] = useState({
    restaurant: true,
    hotel: true,
    attraction: true,
    museum: true,
    park: true,
    cafe: false,
    shopping: false,
    hospital: false,
    fuel: false,
  });
  const [selectedDay, setSelectedDay] = useState(1);
  const { itinerary, addPoi, updateItinerary } = useContext(ItineraryContext) || {};
  const [routeInfo, setRouteInfo] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);

  // Get browser geolocation on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCenter({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => console.warn("Geolocation denied, using default"),
      );
    }
  }, []);

  const fetchPois = useCallback(async (lat, lng) => {
    const enabledCategories = Object.entries(categoryFilters)
      .filter(([, v]) => v)
      .map(([k]) => k);
    if (!enabledCategories.length) return [];
    const params = new URLSearchParams({
      lat,
      lng,
      radius: "1000",
    });
    enabledCategories.forEach((c) => params.append("category", c));
    const resp = await fetch(`${window.location.origin}/api/nearby?${params.toString()}`);
    if (!resp.ok) throw new Error("API error");
    return await resp.json();
  }, [categoryFilters]);

  // Map move handler updates center & fetches POIs
  function MapEventsHandler() {
    useMapEvents({
      moveend: (e) => {
        const map = e.target;
        const c = map.getCenter();
        setCenter({ lat: c.lat, lng: c.lng });
      },
    });
    return null;
  }

  const [pois, setPois] = useState([]);
  useEffect(() => {
    fetchPois(center.lat, center.lng).then(setPois).catch(() => setPois([]));
  }, [center, fetchPois]);

  const handleShowRoute = async (poi) => {
    setLoadingRoute(true);
    const origin = itinerary?.find((s) => s.day === selectedDay && s.order === 1) || { lat: center.lat, lng: center.lng };
    const resp = await fetch(
      `${window.location.origin}/api/route?origin_lat=${origin.lat}&origin_lng=${origin.lng}&dest_lat=${poi.lat}&dest_lng=${poi.lng}&mode=driving`
    );
    const data = await resp.json();
    setRouteInfo(data);
    setLoadingRoute(false);
  };

  return (
    <div className="map-wrapper">
      <FilterPanel filters={categoryFilters} setFilters={setCategoryFilters} />
      <DayTabs selectedDay={selectedDay} setSelectedDay={setSelectedDay} />
      <MapContainer center={[center.lat, center.lng]} zoom={14} style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapEventsHandler />
        <MapView pois={pois} onShowRoute={handleShowRoute} addPoi={addPoi} />
        {routeInfo && <RouteLayer routeInfo={routeInfo} />}
        {itinerary && <ItineraryMarkers itinerary={itinerary} selectedDay={selectedDay} />}
      </MapContainer>
      {loadingRoute && <LoadingOverlay message="Calculating Route..." />}
    </div>
  );
}
