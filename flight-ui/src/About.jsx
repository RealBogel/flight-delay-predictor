import React from "react";

export default function About() {
  return (
    <main style={{ background: "#0f172a", minHeight: "100vh" , paddingTop: "80px"}}>
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 16px", color: "#cbd5e1", fontFamily: "system-ui, sans-serif" }}>
        <h1 style={{ color: "white", marginTop: 0 }}>Welcome to my Flight Delay Predictor ✈️</h1>
        <p>
          This project combines my interests in machine learning and full-stack development.
        </p>
        <p>
         I built a model that predicts whether a flight is likely to be delayed, using real-time
         flight and weather data. The backend runs on Django and serves predictions from an
         XGBoost model, while the frontend is powered by React and shows results with a live gauge visualization.
        </p>
        <p>
         The app is designed to be simple for anyone to use: just enter a flight number and date, and you'll
         see the predicted delay risk.
        </p>
      </div>
    </main>
  );
}