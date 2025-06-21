// Layout for the normal non-landing pages

// src/components/Layout.tsx
import { Header } from "@/elements/header";
//import { Route, Routes } from "react-router-dom";
import { BrowserRouter, Routes, Route } from "react-router";

import { useAuth } from "../contextproviders/authprovider";
import { Skeleton } from "@/components/ui/skeleton";
import { Navigate } from "react-router-dom";

import search from "@/pages/SearchPage";
import selectcontent from "@/pages/selectcontent";
import summaryviewing from "@/pages/SummaryViewing";
import questionandanswers from "@/pages/QnAPage";
import about from "@/pages/About";

// Define props type for TypeScript (optional but recommended)
type LayoutProps = {
	children: React.ReactNode;
};

// export function Layout( {children}: LayoutProps ) {
export function Layout({ children }: { children: React.ReactNode }) {
	const { user, loading } = useAuth();
	if (loading) {
		return (
			// use skeleton
			<div className="flex flex-col space-y-3">
				<Skeleton className="h-[125px] w-[250px] rounded-xl" />
				<div className="space-y-2">
					<Skeleton className="h-4 w-[250px]" />
					<Skeleton className="h-4 w-[200px]" />
				</div>
			</div>
		);
	}
	if (!user) return <Navigate to="/nopage" />;

	return (
		<div style={{ textAlign: "center" }}>
			<div className="min-h-screen">
				<Header />

				<Routes>
					<Route
						path="/"
						element={
							<div>
								Welcome! You are a viewing as a{" "}
								{user.role === "dev" ? "developer" : "manager"} the repository{" "}
								{user.reponame}.
							</div>
						}
					/>
					<Route path="/selectcontent" element={{ selectcontent }} />
					<Route path="/summaryviewing" element={{ summaryviewing }} />
					<Route path="/questionandanswers" element={{ questionandanswers }} />
					<Route path="/search" element={{ search }} />
					<Route path="/about" element={{ about }} />
				</Routes>

				<main className="pt-16">
					{" "}
					{/* Add padding to account for fixed header */}
					{children}
				</main>
			</div>
		</div>
	);
}
