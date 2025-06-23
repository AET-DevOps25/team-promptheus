// Layout for the normal non-landing pages
import { Route, Routes } from "react-router";
import { Navigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
// src/components/Layout.tsx
import { Header } from "@/elements/header";
import about from "@/pages/About";
import questionandanswers from "@/pages/QnAPage";
import search from "@/pages/SearchPage";
import summaryviewing from "@/pages/SummaryViewing";
import selectcontent from "@/pages/selectcontent";
import { useAuth } from "../contextproviders/authprovider";

type LayoutProps = {
	children: React.ReactNode;
};

export function Layout({ children }: LayoutProps) {
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
						element={
							<div>
								Welcome! You are a viewing as a{" "}
								{user.role === "dev" ? "developer" : "manager"} the repository{" "}
								{user.reponame}.
							</div>
						}
						path="/"
					/>
					<Route element={{ selectcontent }} path="/selectcontent" />
					<Route element={{ summaryviewing }} path="/summaryviewing" />
					<Route element={{ questionandanswers }} path="/questionandanswers" />
					<Route element={{ search }} path="/search" />
					<Route element={{ about }} path="/about" />
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
