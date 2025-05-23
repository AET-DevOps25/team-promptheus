
import React from "react";
import { Link } from "react-router-dom";


export function Header() {
    return (
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-100">
        <div className="container mx-auto px-4 py-3">
          <h1 className="text-xl font-light tracking-tight">
            <span className="font-medium">Auto</span>Pulse
          </h1>
        </div>


            <nav>
            <ul style={{ listStyleType: "none", padding: 0 }}>
                <li>
                <Link to="/">Home</Link>
                </li>
                <li>
                <Link to="/selectcontent">Select content for summary</Link>
                </li>
                <li>
                <Link to="/summaryviewing">View summary for last week</Link>
                </li>
                <li>
                <Link to="/questionandanswers">Q&A</Link>
                </li>
                <li>
                <Link to="/about">About</Link>
                </li>
            </ul>
            </nav>

      </header>
    );
  }


