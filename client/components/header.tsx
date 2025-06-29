"use client";

import { Search, Zap, LogOut, User } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { SearchModal } from "./search-modal";
import { useUser } from "@/hooks/use-user";

export function Header() {
	const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
	const pathname = usePathname();
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

	return (
		<header className="border-b bg-white/80 backdrop-blur-sm">
			<div className="container mx-auto px-4 py-4">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2">
						<Link
							className="flex items-center gap-2 hover:opacity-80 transition-opacity"
							href="/"
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
									<span className="text-sm text-slate-600">
										{userId}
									</span>
									{!isAuthenticated && (
										<span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
											Demo
										</span>
									)}
								</div>
								{isAuthenticated && (
									<Button
										variant="ghost"
										size="sm"
										onClick={clearUser}
										className="text-slate-600 hover:text-slate-900"
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
