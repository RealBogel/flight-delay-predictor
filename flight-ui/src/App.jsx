import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import PredictForm from "./PredictForm";
import About from "./About";
import NavBar from "./NavBar";

export default function App() {
  const basename = import.meta.env.BASE_URL || "/";

  return (
    <BrowserRouter basename={basename}>
      <NavBar />
      <Routes>
        <Route path="/" element={<PredictForm />} />
        <Route path="/about" element={<About />} />
        {/* Fallback to predictor for unknown paths */}
        <Route path="*" element={<PredictForm />} />
      </Routes>
    </BrowserRouter>
  );
}