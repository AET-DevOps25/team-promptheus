
import React from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./auth";


const navItems = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About" },
  { href: "/qna", label: "Q/A" },
  { href: "/search", label: "Search" },
  { href: "/selectcontent", label: "Select content"}
]


export function Header() {

    const { user, loading } = useAuth();
    let location = useLocation();

    return (
      <div>
    <header className="w-full max-w-4xl mx-auto mb-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b">
          
          
          <h1 className="text-3xl font-bold tracking-tight"><span className="font-medium">Auto</span>Pulse</h1>
          
          
        <div> Repository: {user?.reponame}</div>

          <nav className="flex flex-wrap gap-1">
            {navItems.map((item) => (
              <Link
                to={item.href}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  location.pathname === item.href
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
    </header>

        <Outlet />

    </div>

    );
  }


