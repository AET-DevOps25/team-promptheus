"use client";

import { LogOut, Search, User, Zap } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useUser } from "@/contexts/user-context";
import { SearchModal } from "./search-modal";

export function Header() {
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { userId, isAuthenticated, clearUser } = useUser();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchModalOpen(true);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleLogout = () => {
    clearUser();
    router.push("/login");
  };

  return (
    <header className="border-b bg-white/80 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link
              className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              href={isAuthenticated ? "/dashboard" : "/"}
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900">
                <Zap className="h-5 w-5 text-white" />
              </div>
              <h1 className="text-xl font-bold">Prompteus</h1>
            </Link>
          </div>

          {pathname !== "/" && (
            <div className="flex items-center gap-4">
              {/* Quick Search Button */}
              <Button
                className="hidden md:flex items-center gap-2 w-96 justify-start text-muted-foreground"
                onClick={() => setIsSearchModalOpen(true)}
                variant="outline"
              >
                <Search className="h-4 w-4" />
                <span>Search...</span>
                <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </Button>

              <nav className="flex items-center gap-4">
                <Link
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                  href="/dashboard"
                >
                  Dashboard
                </Link>
                <Link
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                  href="/developer"
                >
                  Developer
                </Link>
                <Link
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                  href="/summaries"
                >
                  Summaries
                </Link>
                <Link
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                  href="/qa"
                >
                  Q&A
                </Link>
                <Link
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                  href="/settings"
                >
                  Settings
                </Link>
              </nav>

              {/* User Info and Logout */}
              <div className="flex items-center gap-2 border-l pl-4">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-slate-600" />
                  <span className="text-sm text-slate-600">{userId || "Not logged in"}</span>
                  {!isAuthenticated && (
                    <span className="text-xs text-slate-600 bg-slate-50 px-2 py-1 rounded">
                      Anonymous
                    </span>
                  )}
                </div>
                {isAuthenticated && userId && (
                  <Button
                    className="text-slate-600 hover:text-slate-900"
                    onClick={handleLogout}
                    size="sm"
                    variant="ghost"
                  >
                    <LogOut className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      <SearchModal
        isOpen={isSearchModalOpen}
        onCloseAction={() => setIsSearchModalOpen(false)}
        usercode={userId}
      />
    </header>
  );
}
