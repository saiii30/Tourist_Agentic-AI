import React from "react";

export default function FilterPanel({ filters, setFilters }) {
  const toggle = (key) => {
    setFilters({ ...filters, [key]: !filters[key] });
  };
  const categories = Object.keys(filters);
  return (
    <div className="filter-panel">
      {categories.map((cat) => (
        <div
          key={cat}
          className={`chip ${filters[cat] ? "active" : ""}`}
          onClick={() => toggle(cat)}
        >
          {cat.charAt(0).toUpperCase() + cat.slice(1)}
        </div>
      ))}
    </div>
  );
}
