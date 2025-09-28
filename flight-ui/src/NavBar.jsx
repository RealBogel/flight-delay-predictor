import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function NavBar() {
  const { pathname } = useLocation();

  return (
    <header className="navbar">
      <div className="nav-inner">
        <span className="brand-link">Flight Predictor</span>
        <nav className="links">
          <Link to="/" className={pathname === "/" ? "active" : ""}>Predict</Link>
          <Link to="/about" className={pathname.startsWith("/about") ? "active" : ""}>About</Link>
          <a
            href="https://www.linkedin.com/in/tristan-suwito-9882ba319/"
            target="_blank"
            rel="noreferrer"
          >
            LinkedIn
          </a>
        </nav>
      </div>
    </header>
  );
}