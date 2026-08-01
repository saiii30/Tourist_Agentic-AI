import React from "react";

export default function DayTabs({ selectedDay, setSelectedDay }) {
  const days = [1, 2, 3]; // placeholder, could be dynamic
  return (
    <div className="day-tabs">
      {days.map((d) => (
        <div
          key={d}
          className={`day-tab ${selectedDay === d ? "active" : ""}`}
          onClick={() => setSelectedDay(d)}
        >
          Day {d}
        </div>
      ))}
    </div>
  );
}
