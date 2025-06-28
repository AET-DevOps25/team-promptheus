"use client";

import {
	BarChart3,
	Calendar,
	Clock,
	GitBranch,
	Loader2,
	MessageSquare,
	Search,
	User,
	Users,
} from "lucide-react";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { SearchModal } from "@/components/search-modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { WeeklySummaryServer } from "@/components/weekly-summary-server";
import { useContributions } from "@/lib/api/contributions";

export default function DashboardPage() {
	const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
	// todo: get from local storage
	const userId = "abc";
	const [stats, setStats] = useState({
		activeRepos: 0,
		avgResponseTime: "0h",
		teamMembers: 0,
		weeklyChange: 0,
		weeklyCommits: 0,
	});
	const [isLoading, setIsLoading] = useState(true);

	// Fetch contributions data
	const { data: contributionsData } = useContributions(
		{
			pageable: {
				page: 0,
				size: 100,
				sort: ["createdAt,desc"],
			},
		},
		true,
	);

	// Process contributions data to extract dashboard stats
	useEffect(() => {
		if (contributionsData?.content) {
			setIsLoading(false);

			// Calculate stats from contributions
			const repos = new Set();
			const users = new Set();
			const thisWeekStart = new Date();
			thisWeekStart.setDate(thisWeekStart.getDate() - 7);

			let weeklyCommits = 0;
			let totalResponseTime = 0;
			let prCount = 0;

			contributionsData.content.forEach((contribution) => {
				// Count unique repositories
				repos.add(contribution.gitRepositoryId);

				// Count unique contributors
				users.add(contribution.username);

				// Count commits from the last week
				if (
					contribution.type.includes("Commit") &&
					contribution.createdAt &&
					new Date(contribution.createdAt) >= thisWeekStart
				) {
					weeklyCommits++;
				}

				// Calculate average PR review time (simplified example)
				if (contribution.type.includes("PullRequest")) {
					prCount++;
					totalResponseTime += 2.4; // Using placeholder for demo
				}
			});

			// Previous week comparison (simplified example)
			const previousWeeklyCommits = Math.max(weeklyCommits - 2, 0);
			const weeklyChange = weeklyCommits - previousWeeklyCommits;

			// Average response time
			const avgResponseHours =
				prCount > 0 ? (totalResponseTime / prCount).toFixed(1) : "2.4";

			setStats({
				activeRepos: repos.size,
				avgResponseTime: `${avgResponseHours}h`,
				teamMembers: users.size,
				weeklyChange,
				weeklyCommits,
			});
		}
	}, [contributionsData]);
	return (
		<>
			<header className="border-b bg-white">
				<div className="container mx-auto px-4 py-4">
					<h1 className="text-2xl font-bold">Dashboard - {userId}</h1>
					<p className="text-slate-600">Your AI-powered GitHub insights</p>
				</div>
			</header>

			<main className="container mx-auto px-4 py-8">
				<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">
								Active Repositories
							</CardTitle>
							<GitBranch className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							{isLoading ? (
								<div className="flex items-center">
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									<span className="text-sm text-muted-foreground">
										Loading...
									</span>
								</div>
							) : (
								<>
									<div className="text-2xl font-bold">{stats.activeRepos}</div>
									<p className="text-xs text-muted-foreground">
										From all contributions
									</p>
								</>
							)}
						</CardContent>
					</Card>

					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">
								Team Members
							</CardTitle>
							<Users className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							{isLoading ? (
								<div className="flex items-center">
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									<span className="text-sm text-muted-foreground">
										Loading...
									</span>
								</div>
							) : (
								<>
									<div className="text-2xl font-bold">{stats.teamMembers}</div>
									<p className="text-xs text-muted-foreground">
										Across all projects
									</p>
								</>
							)}
						</CardContent>
					</Card>

					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">This Week</CardTitle>
							<BarChart3 className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							{isLoading ? (
								<div className="flex items-center">
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									<span className="text-sm text-muted-foreground">
										Loading...
									</span>
								</div>
							) : (
								<>
									<div className="text-2xl font-bold">
										{stats.weeklyCommits}
									</div>
									<p className="text-xs text-muted-foreground">
										{stats.weeklyChange > 0
											? `+${stats.weeklyChange} from last week`
											: stats.weeklyChange < 0
												? `${stats.weeklyChange} from last week`
												: "Same as last week"}
									</p>
								</>
							)}
						</CardContent>
					</Card>

					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">
								Avg Response
							</CardTitle>
							<Clock className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							{isLoading ? (
								<div className="flex items-center">
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									<span className="text-sm text-muted-foreground">
										Loading...
									</span>
								</div>
							) : (
								<>
									<div className="text-2xl font-bold">
										{stats.avgResponseTime}
									</div>
									<p className="text-xs text-muted-foreground">
										PR review time
									</p>
								</>
							)}
						</CardContent>
					</Card>
				</div>

				<div className="mt-8 grid gap-8 lg:grid-cols-2">
					{/* Left Column */}
					<div className="space-y-8">
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Search className="h-5 w-5" />
									Quick Search
								</CardTitle>
								<CardDescription>
									Find anything across your repositories with AI-powered
									semantic search
								</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="flex gap-4">
									<Button
										className="flex-1 justify-start text-muted-foreground"
										onClick={() => setIsSearchModalOpen(true)}
										variant="outline"
									>
										<Search className="h-4 w-4 mr-2" />
										Search commits, PRs, issues...
										<kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
											<span className="text-xs">⌘</span>K
										</kbd>
									</Button>
								</div>
								<SearchModal
									isOpen={isSearchModalOpen}
									onCloseAction={() => setIsSearchModalOpen(false)}
									usercode={userId}
								/>
							</CardContent>
						</Card>

						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<MessageSquare className="h-5 w-5" />
									Recent Q&A
								</CardTitle>
								<CardDescription>
									Latest questions and AI-powered answers about your
									repositories
								</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-3">
									<div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
										<div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100">
											<User className="h-3 w-3 text-blue-600" />
										</div>
										<div className="flex-1 min-w-0">
											<p className="text-sm font-medium">
												What are the main performance bottlenecks?
											</p>
											<p className="text-xs text-muted-foreground mt-1">
												Database queries and memory management issues
												identified...
											</p>
											<div className="flex items-center gap-2 mt-2">
												<Badge className="text-xs" variant="secondary">
													Approved
												</Badge>
												<span className="text-xs text-muted-foreground">
													8 upvotes
												</span>
											</div>
										</div>
									</div>
									<div className="flex gap-2">
										<Button
											asChild
											className="flex-1"
											size="sm"
											variant="outline"
										>
											<Link href="/qa">View All Q&A</Link>
										</Button>
										<Button asChild className="flex-1" size="sm">
											<Link href="/qa">Ask Question</Link>
										</Button>
									</div>
								</div>
							</CardContent>
						</Card>

						<Card>
							<CardHeader>
								<CardTitle>Recent Activity</CardTitle>
								<CardDescription>
									AI-generated summary of your team's progress
								</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									<div className="flex items-start gap-3">
										<Badge variant="secondary">Done</Badge>
										<div>
											<p className="font-medium">
												Authentication system refactor completed
											</p>
											<p className="text-sm text-muted-foreground">
												3 PRs merged, 2 issues closed
											</p>
										</div>
									</div>
									<div className="flex items-start gap-3">
										<Badge variant="outline">In Progress</Badge>
										<div>
											<p className="font-medium">
												API rate limiting implementation
											</p>
											<p className="text-sm text-muted-foreground">
												2 active PRs, estimated completion: Friday
											</p>
										</div>
									</div>
									<div className="flex items-start gap-3">
										<Badge variant="destructive">Blocked</Badge>
										<div>
											<p className="font-medium">Database migration pending</p>
											<p className="text-sm text-muted-foreground">
												Waiting for infrastructure team approval
											</p>
										</div>
									</div>
								</div>
							</CardContent>
						</Card>
					</div>

					{/* Right Column - Weekly Summary */}
					<div>
						<Suspense
							fallback={
								<Card>
									<CardHeader>
										<div className="flex items-center gap-2">
											<Calendar className="h-5 w-5" />
											<div className="h-6 w-48 bg-slate-200 rounded animate-pulse" />
										</div>
										<div className="h-4 w-80 bg-slate-100 rounded animate-pulse" />
									</CardHeader>
									<CardContent>
										<div className="space-y-4">
											<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
												{Array.from({ length: 4 }).map((_, i) => (
													<div
														className="text-center p-3 bg-slate-50 rounded-lg"
														key={i}
													>
														<div className="h-8 w-12 mx-auto mb-2 bg-slate-200 rounded animate-pulse" />
														<div className="h-3 w-16 mx-auto bg-slate-100 rounded animate-pulse" />
													</div>
												))}
											</div>
											<div className="h-96 bg-slate-50 rounded-lg animate-pulse" />
										</div>
									</CardContent>
								</Card>
							}
						>
							<WeeklySummaryServer userId={userId} />
						</Suspense>
					</div>
				</div>
			</main>
		</>
	);
}
