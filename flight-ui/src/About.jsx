import React from "react";

export default function About() {
  return (
    <main style={{ background: "#0f172a", minHeight: "100vh" , paddingTop: "80px"}}>
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 16px", color: "#cbd5e1", fontFamily: "system-ui, sans-serif" }}>
        <h1 style={{ color: "white", marginTop: 0 }}>About</h1>
        <p>
          This project predicts flight delay probability using a machine learning
          model served by a Django backend. The React front-end calls
          <code> /api/predict/</code> with a flight number and date, and shows a
          simple gauge.
        </p>
        <p>
          On free data plans, the app may use current conditions or fallback behavior
          to stay responsive. Model version info is returned with each prediction.
        </p>
      </div>
    </main>
  );
}