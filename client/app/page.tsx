"use client";

import {
	BarChart3,
	ExternalLink,
	Github,
	Loader2,
	Search,
	Zap,
} from "lucide-react";
import Link from "next/link";
import type React from "react";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function HomePage() {
	const [pat, setPat] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState("");
	const [links, setLinks] = useState<{
		dashboard: string;
		settings: string;
	} | null>(null);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!pat.trim()) {
			setError("Please enter your GitHub Personal Access Token");
			return;
		}

		setIsLoading(true);
		setError("");

		try {
			// Validate the GitHub PAT directly on the frontend
			const response = await fetch("https://api.github.com/user", {
				headers: {
					Authorization: `token ${pat}`,
					"User-Agent": "Prompteus-App",
				},
			});

			if (!response.ok) {
				throw new Error("Invalid GitHub Personal Access Token");
			}

			const userData = await response.json();
			const userId = userData.login || "user";

			// Set the links after successful validation
			setLinks({
				dashboard: `/dashboard/${userId}`,
				settings: `/settings/${userId}`,
			});
		} catch (err) {
			setError(
				"Invalid token or API error. Please check your Personal Access Token.",
			);
		} finally {
			setIsLoading(false);
		}
	};

	if (links) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
				<Card className="w-full max-w-md">
					<CardHeader className="text-center">
						<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
							<Zap className="h-6 w-6 text-green-600" />
						</div>
						<CardTitle className="text-2xl">Setup Complete!</CardTitle>
						<CardDescription>
							Your GitHub integration is ready. Choose where to go next:
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<Link href={links.dashboard}>
							<Button className="w-full justify-between" size="lg">
								<div className="flex items-center gap-2">
									<BarChart3 className="h-4 w-4" />
									Go to Dashboard
								</div>
								<ExternalLink className="h-4 w-4" />
							</Button>
						</Link>
						<Link href={links.settings}>
							<Button
								className="w-full justify-between"
								size="lg"
								variant="outline"
							>
								<div className="flex items-center gap-2">
									<Github className="h-4 w-4" />
									Repository Settings
								</div>
								<ExternalLink className="h-4 w-4" />
							</Button>
						</Link>
					</CardContent>
				</Card>
			</div>
		);
	}

	// Replace the entire return statement with:
	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
			{/* Main Content */}
			<main className="container mx-auto px-4 py-12">
				<div className="mx-auto max-w-4xl text-center">
					<h2 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
						Better GitHub Interface
						<span className="text-slate-600"> with AI</span>
					</h2>
					<p className="mt-6 text-lg leading-8 text-slate-600 max-w-2xl mx-auto">
						Stop digging through GitHub's search. Get instant, AI-powered
						insights into your repositories, automated progress summaries, and
						semantic search that actually works.
					</p>

					{/* Features */}
					<div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
						<div className="flex flex-col items-center p-6">
							<div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 mb-4">
								<BarChart3 className="h-6 w-6 text-blue-600" />
							</div>
							<h3 className="font-semibold text-slate-900">Auto Summaries</h3>
							<p className="text-sm text-slate-600 mt-2">
								AI-generated progress reports without the Friday writeups
							</p>
						</div>
						<div className="flex flex-col items-center p-6">
							<div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 mb-4">
								<Search className="h-6 w-6 text-green-600" />
							</div>
							<h3 className="font-semibold text-slate-900">Semantic Search</h3>
							<p className="text-sm text-slate-600 mt-2">
								Find code and issues by meaning, not just keywords
							</p>
						</div>
						<div className="flex flex-col items-center p-6">
							<div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 mb-4">
								<Zap className="h-6 w-6 text-purple-600" />
							</div>
							<h3 className="font-semibold text-slate-900">Instant Q&A</h3>
							<p className="text-sm text-slate-600 mt-2">
								Ask questions about your codebase and get immediate answers
							</p>
						</div>
					</div>

					{/* Setup Form */}
					<div className="mt-16 flex justify-center">
						<Card className="w-full max-w-md">
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Github className="h-5 w-5" />
									Get Started
								</CardTitle>
								<CardDescription>
									Enter your GitHub Personal Access Token to begin
								</CardDescription>
							</CardHeader>
							<CardContent>
								<form className="space-y-4" onSubmit={handleSubmit}>
									<div className="space-y-2">
										<Label htmlFor="pat">GitHub Personal Access Token</Label>
										<Input
											disabled={isLoading}
											id="pat"
											onChange={(e) => setPat(e.target.value)}
											placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
											type="password"
											value={pat}
										/>
										<p className="text-xs text-slate-500">
											Need a token?{" "}
											<a
												className="text-blue-600 hover:underline"
												href="https://github.com/settings/tokens"
												rel="noopener noreferrer"
												target="_blank"
											>
												Create one here
											</a>
										</p>
									</div>

									{error && (
										<Alert variant="destructive">
											<AlertDescription>{error}</AlertDescription>
										</Alert>
									)}

									<Button className="w-full" disabled={isLoading} type="submit">
										{isLoading ? (
											<>
												<Loader2 className="mr-2 h-4 w-4 animate-spin" />
												Setting up...
											</>
										) : (
											"Continue"
										)}
									</Button>
								</form>
							</CardContent>
						</Card>
					</div>
				</div>
			</main>
		</div>
	);
}
