import React, { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// A tiny semicircle gauge for probability [0..1]
function Gauge({ value }) {
  const p = Math.max(0, Math.min(1, Number(value || 0)));
  // rotate from LEFT (-90°) to RIGHT (+90°) across the semicircle
  const angle = -90 + p * 180;

  return (
    <div style={{ width: 260, margin: "16px auto" }}>
      <svg viewBox="0 0 200 120" style={{ width: "100%", display: "block" }}>
        {/* background arc */}
        <path d="M10,100 A90,90 0 0,1 190,100" fill="none" stroke="#e5e7eb" strokeWidth="14" />
        {/* 3 colored bands (optional) */}
        <path d="M10,100 A90,90 0 0,1 190,100" fill="none" stroke="#22c55e" strokeWidth="14" strokeDasharray="60 283" />
        <path d="M10,100 A90,90 0 0,1 190,100" fill="none" stroke="#f59e0b" strokeWidth="14" strokeDasharray="60 283" strokeDashoffset="-60" />
        <path d="M10,100 A90,90 0 0,1 190,100" fill="none" stroke="#ef4444" strokeWidth="14" strokeDasharray="60 283" strokeDashoffset="-120" />

        {/* needle:
            center of arc is (100,100). We draw a vertical line up, then rotate it. */}
        <g transform={`rotate(${angle} 100 100)`} style={{ transition: "transform 300ms ease" }}>
          <line x1="100" y1="100" x2="100" y2="20"
            stroke="#ffffff" strokeWidth="4" strokeLinecap="round" />
          <circle cx="100" cy="100" r="7" fill="#ffffff" />
        </g>
      </svg>

      <div style={{ textAlign: "center", marginTop: 8, fontFamily: "system-ui, sans-serif" }}>
        <div style={{ fontSize: 18, fontWeight: 600 }}>{(p * 100).toFixed(1)}% delay risk</div>
        <div style={{ fontSize: 12, color: "#6b7280" }}>(≥ 50% → delayed)</div>
      </div>
    </div>
  );
}

export default function PredictForm() {
  // Form state (inputs)
  const [flightNumber, setFlightNumber] = useState("UA245");
  const [flightDate, setFlightDate] = useState(new Date().toISOString().slice(0, 10));
  // Result + error state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");

  const planeSrc = `${import.meta.env.BASE_URL}airplane.gif`;
  const bgUrl = `${import.meta.env.BASE_URL}your-background.jpg`;

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setErr("");
    setResult(null);
    try {
      // Call your Django API
      const res = await fetch(`${API_URL}/api/predict/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flight_number: flightNumber, flight_date: flightDate }),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`);
      setResult(data); // { delayed_probability, delayed_label, model_version }
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="predict-page">
      {/* Airplane gif above the card */}
      <div className="page" style={{ display:'flex', flexDirection:'column', alignItems:'center' }}>

        <div
          style={{
            maxWidth: 520,
            width: "100%",
            padding: 16,
            background: "#1f2937",
            borderRadius: 12,
            color: "white",
            boxShadow: "0 10px 20px rgba(0,0,0,0.25)",
          }}
        >
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12, color: "white" }}>
            Flight Delay Predictor
          </h1>

          <img
            src={planeSrc}
            alt="Airplane animation"
            style={{
              display: "block",
              margin: "8px auto 16px", // centered with space below
              width: 450,              // tweak as you like
              height: "auto",
            }}
          />

          {/* The input form */}
          <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>Flight number (e.g., UA245)</span>
              <input
                value={flightNumber}
                onChange={(e) => setFlightNumber(e.target.value.toUpperCase())}
                required
                style={{ padding: 10, border: "1px solid #d1d5db", borderRadius: 8 }}
                placeholder="AA100"
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>Flight date (YYYY-MM-DD)</span>
              <input
                type="date"
                value={flightDate}
                onChange={(e) => setFlightDate(e.target.value)}
                required
                style={{ padding: 10, border: "1px solid #d1d5db", borderRadius: 8 }}
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              style={{
                padding: "10px 14px",
                background: "#111827",
                color: "white",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Predicting..." : "Predict"}
            </button>
          </form>

          {/* Error message */}
          {err && (
            <div style={{ marginTop: 16, color: "#b91c1c", background: "#fee2e2", padding: 10, borderRadius: 8 }}>
              {err}
            </div>
          )}

          {/* Result display */}
          {result && (
            <div style={{ marginTop: 16, padding: 16, border: "1px solid #e5e7eb", borderRadius: 12 }}>
              <Gauge value={result.delayed_probability} />
              <div style={{ display: "grid", gap: 6, textAlign: "center" }}>
                <div>
                  <strong>Label:</strong> {Number(result.delayed_label) === 1 ? "Delayed" : "On time"}
                </div>
                <div>
                  <strong>Model:</strong> {result.model_version || "unknown"}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}