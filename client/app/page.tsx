"use client";

import {
	ArrowRight,
	CheckCircle,
	Github,
	Loader2,
	MessageSquare,
	Search,
	TrendingUp,
	Users,
	Zap,
} from "lucide-react";
import { useId, useState } from "react";
import { Badge } from "@/components/ui/badge";
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
	const [repoLink, setRepoLink] = useState("");
	const [pat, setPat] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const repoLinkId = useId();
	const patId = useId();

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!repoLink.trim() || !pat.trim()) return;

		setIsLoading(true);
		try {
			// In a real app, this would make an API call to set up the repository
			await new Promise((resolve) => setTimeout(resolve, 2000)); // Simulate API call

			// For demo purposes, just redirect to a demo dashboard
			const userCode = repoLink.split("/").pop() || "demo";
			localStorage.setItem("usercode", userCode);
			window.location.href = "/dashboard";
		} catch (error) {
			console.error("Setup error:", error);
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
			{/* Header */}
			<header className="border-b bg-white/80 backdrop-blur-sm">
				<div className="container mx-auto px-4 py-4">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-4">
							<div className="flex items-center gap-2">
								<div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
									<Zap className="h-5 w-5 text-white" />
								</div>
								<span className="text-xl font-bold text-slate-900">
									Prompteus
								</span>
							</div>
						</div>
						<Button asChild size="sm" variant="outline">
							<a href="/login">
								<Users className="h-4 w-4 mr-2" />
								Sign In
							</a>
						</Button>
					</div>
				</div>
			</header>

			<main className="container mx-auto px-4 py-16 max-w-6xl">
				<div className="space-y-24">
					{/* Hero Section */}
					<section className="text-center space-y-8">
						<div className="space-y-4">
							<Badge className="bg-blue-100 text-blue-800" variant="secondary">
								✨ AI-Powered GitHub Management
							</Badge>
							<h1 className="text-4xl md:text-6xl font-bold text-slate-900">
								Keep up with{" "}
								<span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
									team changes
								</span>{" "}
								effortlessly
							</h1>
							<p className="text-xl text-slate-600 max-w-3xl mx-auto">
								Prompteus uses AI to summarize repository activity, answer
								questions about your codebase, and keep diverse teams aligned
								with intelligent insights.
							</p>
						</div>

						<div className="flex flex-col sm:flex-row gap-4 justify-center">
							<Button className="text-lg px-8 py-6" size="lg">
								<Github className="h-5 w-5 mr-2" />
								Get Started Free
							</Button>
							<Button className="text-lg px-8 py-6" size="lg" variant="outline">
								<MessageSquare className="h-5 w-5 mr-2" />
								See Demo
							</Button>
						</div>
					</section>

					{/* Features Grid */}
					<section className="grid md:grid-cols-3 gap-8">
						<Card className="text-center">
							<CardHeader>
								<TrendingUp className="h-12 w-12 text-blue-600 mx-auto mb-4" />
								<CardTitle>Smart Summaries</CardTitle>
								<CardDescription>
									AI-generated weekly summaries of repository activity, pull
									requests, and team progress.
								</CardDescription>
							</CardHeader>
						</Card>

						<Card className="text-center">
							<CardHeader>
								<Search className="h-12 w-12 text-green-600 mx-auto mb-4" />
								<CardTitle>Intelligent Q&A</CardTitle>
								<CardDescription>
									Ask questions about your codebase and get instant,
									context-aware answers powered by AI.
								</CardDescription>
							</CardHeader>
						</Card>

						<Card className="text-center">
							<CardHeader>
								<Users className="h-12 w-12 text-purple-600 mx-auto mb-4" />
								<CardTitle>Team Alignment</CardTitle>
								<CardDescription>
									Keep everyone informed about changes, decisions, and progress
									across multiple repositories.
								</CardDescription>
							</CardHeader>
						</Card>
					</section>

					{/* Setup Form */}
					<section className="max-w-2xl mx-auto">
						<Card>
							<CardHeader className="text-center">
								<CardTitle className="text-2xl">
									Connect Your Repository
								</CardTitle>
								<CardDescription className="text-lg">
									Get started with AI-powered insights for your GitHub
									repository in under 2 minutes.
								</CardDescription>
							</CardHeader>
							<CardContent>
								<form className="space-y-6" onSubmit={handleSubmit}>
									<div className="space-y-2">
										<Label htmlFor={repoLinkId}>GitHub Repository Link</Label>
										<Input
											disabled={isLoading}
											id={repoLinkId}
											onChange={(e) => setRepoLink(e.target.value)}
											placeholder="https://github.com/username/repository"
											required
											type="url"
											value={repoLink}
										/>
									</div>
									<div className="space-y-2">
										<Label htmlFor={patId}>GitHub Personal Access Token</Label>
										<Input
											disabled={isLoading}
											id={patId}
											onChange={(e) => setPat(e.target.value)}
											placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
											required
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
											</a>{" "}
											with 'repo' permissions.
										</p>
									</div>
									<Button
										className="w-full text-lg py-6"
										disabled={!repoLink.trim() || !pat.trim() || isLoading}
										size="lg"
										type="submit"
									>
										{isLoading ? (
											<>
												<Loader2 className="h-5 w-5 mr-2 animate-spin" />
												Setting up your repository...
											</>
										) : (
											<>
												<ArrowRight className="h-5 w-5 mr-2" />
												Start Analyzing Repository
											</>
										)}
									</Button>
								</form>

								<div className="mt-6 p-4 bg-green-50 rounded-lg">
									<div className="flex items-center gap-2 text-green-800 mb-2">
										<CheckCircle className="h-5 w-5" />
										<span className="font-medium">What happens next?</span>
									</div>
									<ul className="text-sm text-green-700 space-y-1 ml-7">
										<li>
											• We'll analyze your repository structure and recent
											activity
										</li>
										<li>• Generate your first AI summary within minutes</li>
										<li>• Set up intelligent Q&A for your codebase</li>
										<li>• Create your personalized dashboard</li>
									</ul>
								</div>
							</CardContent>
						</Card>
					</section>

					{/* Trust Indicators */}
					<section className="text-center space-y-8">
						<h2 className="text-2xl font-bold text-slate-900">
							Trusted by Development Teams
						</h2>
						<div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
							<div className="space-y-2">
								<div className="text-3xl font-bold text-blue-600">10k+</div>
								<p className="text-slate-600">Repositories Analyzed</p>
							</div>
							<div className="space-y-2">
								<div className="text-3xl font-bold text-green-600">50k+</div>
								<p className="text-slate-600">AI Summaries Generated</p>
							</div>
							<div className="space-y-2">
								<div className="text-3xl font-bold text-purple-600">99.9%</div>
								<p className="text-slate-600">Uptime Reliability</p>
							</div>
						</div>
					</section>

					{/* CTA Section */}
					<section className="text-center space-y-6 py-16 bg-gradient-to-r from-blue-50 to-purple-50 rounded-3xl">
						<h2 className="text-3xl font-bold text-slate-900">
							Ready to transform your team's workflow?
						</h2>
						<p className="text-lg text-slate-600 max-w-2xl mx-auto">
							Join thousands of developers who use Prompteus to stay aligned and
							productive. Start your free trial today.
						</p>
						<Button className="text-lg px-8 py-6" size="lg">
							<Github className="h-5 w-5 mr-2" />
							Start Free Trial
						</Button>
					</section>
				</div>
			</main>

			{/* Footer */}
			<footer className="border-t bg-white/80 backdrop-blur-sm mt-24">
				<div className="container mx-auto px-4 py-8">
					<div className="text-center text-sm text-slate-500">
						<p>
							© 2024 Prompteus. Making GitHub management effortless with AI.
						</p>
					</div>
				</div>
			</footer>
		</div>
	);
}
