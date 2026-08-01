import React from "react";

export default function LoadingOverlay({ message }) {
  return (
    <div className="loader-overlay">
      <div>{message || "Loading..."}</div>
    </div>
  );
}
