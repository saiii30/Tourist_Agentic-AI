// src/pages/TripPlanner.jsx
import React, { useEffect, useState } from "react";
import MapComponent from "../components/MapComponent";
import "../styles/map.css";

export default function TripPlanner() {
  const [trips, setTrips] = useState([]);
  const [loadingTrips, setLoadingTrips] = useState(false);

  const fetchTrips = async () => {
    setLoadingTrips(true);
    try {
      const resp = await fetch(`${window.location.origin}/trips`);
      if (!resp.ok) throw new Error("Failed to fetch trips");
      const data = await resp.json();
      setTrips(data);
    } catch (e) {
      console.error(e);
      setTrips([]);
    } finally {
      setLoadingTrips(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  return (
    <div className="trip-planner-page" style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header className="header" style={{ padding: "1rem", background: "linear-gradient(135deg, #1e1e2f, #354259)", color: "#fff", textAlign: "center", fontFamily: "'Inter', sans-serif" }}>
        <h1>TouristAI Trip Planner</h1>
      </header>
      <main style={{ flex: 1, display: "flex" }}>
        {/* Left pane: list of trips */}
        <aside className="trip-list" style={{ width: "300px", overflowY: "auto", background: "#f7f9fc", padding: "1rem" }}>
          <h2 style={{ fontFamily: "'Inter', sans-serif" }}>Your Trips</h2>
          {loadingTrips ? (
            <p>Loading trips…</p>
          ) : trips.length === 0 ? (
            <p>No trips yet. Create one via the API.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {trips.map((t) => (
                <li key={t.id} style={{ marginBottom: "0.5rem", borderBottom: "1px solid #ddd", paddingBottom: "0.5rem" }}>
                  <strong>{t.name}</strong>
                  <br />
                  {t.description}
                </li>
              ))}
            </ul>
          )}
        </aside>
        {/* Right pane: interactive map */}
        <section className="map-section" style={{ flex: 1, position: "relative" }}>
          <MapComponent />
        </section>
      </main>
    </div>
  );
}
