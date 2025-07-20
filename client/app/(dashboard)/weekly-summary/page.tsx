"use client";

import {
	Calendar,
	Clock,
	Download,
	FileText,
	Loader2,
	Users,
} from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { WeeklySummaryServer } from "@/components/weekly-summary-server";
import { useUser } from "@/contexts/user-context";
import { toast } from "@/hooks/use-toast";
import { useGenerateSummary, useSummaries } from "@/lib/api/summary";

function RecentSummaries() {
	// Fetch actual summaries from the API
	const {
		data: summariesPage,
		isLoading,
		error,
	} = useSummaries({
		size: 5,
		sort: ["createdAt,desc"],
	});

	const summaries = summariesPage?.content || [];

	if (isLoading) {
		return (
			<Card>
				<CardHeader>
					<div className="flex items-center gap-2">
						<FileText className="h-5 w-5" />
						<CardTitle className="text-lg">Recent Summaries</CardTitle>
					</div>
				</CardHeader>
				<CardContent>
					<div className="space-y-3">
						{Array.from(
							{ length: 3 },
							(_, i) => `recent-summary-skeleton-${i + 1}`,
						).map((key) => (
							<div
								className="flex items-center gap-3 p-3 border rounded animate-pulse"
								key={key}
							>
								<div className="h-8 w-8 bg-slate-200 rounded" />
								<div className="flex-1">
									<div className="h-4 w-2/3 bg-slate-200 rounded mb-1" />
									<div className="h-3 w-1/2 bg-slate-100 rounded" />
								</div>
								<div className="h-6 w-6 bg-slate-200 rounded" />
							</div>
						))}
					</div>
				</CardContent>
			</Card>
		);
	}

	if (error) {
		return (
			<Card>
				<CardHeader>
					<div className="flex items-center gap-2">
						<FileText className="h-5 w-5" />
						<CardTitle className="text-lg">Recent Summaries</CardTitle>
					</div>
				</CardHeader>
				<CardContent>
					<div className="text-center py-8">
						<FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
						<p className="text-muted-foreground">Failed to load summaries</p>
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			<CardHeader>
				<div className="flex items-center gap-2">
					<FileText className="h-5 w-5" />
					<CardTitle className="text-lg">Recent Summaries</CardTitle>
				</div>
			</CardHeader>
			<CardContent>
				<div className="space-y-3">
					{summaries.length > 0 ? (
						summaries.map((summary) => (
							<Link
								href={`/summary/${summary.id}`}
								key={summary.id}
								className="block"
							>
								<div className="flex items-center gap-3 p-3 border rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
									<div className="flex h-8 w-8 items-center justify-center rounded bg-blue-100">
										<FileText className="h-4 w-4 text-blue-600" />
									</div>
									<div className="flex-1 min-w-0">
										<p className="font-medium text-sm truncate">
											{summary.username} - Week {summary.week}
										</p>
										<div className="flex items-center gap-2 text-xs text-muted-foreground">
											<span>
												{summary.totalContributions || 0} contributions
											</span>
											<span>•</span>
											<span>
												{summary.createdAt
													? new Date(summary.createdAt).toLocaleDateString()
													: "Unknown date"}
											</span>
											{summary.repositoryName && (
												<>
													<span>•</span>
													<span className="truncate max-w-32">
														{summary.repositoryName}
													</span>
												</>
											)}
										</div>
									</div>
									<Button size="sm" variant="ghost">
										<Download className="h-3 w-3" />
									</Button>
								</div>
							</Link>
						))
					) : (
						<div className="text-center py-8">
							<FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
							<p className="text-muted-foreground">No summaries found</p>
							<p className="text-xs text-muted-foreground mt-1">
								Generated summaries will appear here
							</p>
						</div>
					)}
				</div>
			</CardContent>
		</Card>
	);
}

function SummariesTimeline() {
	const {
		data: summariesPage,
		isLoading,
		error,
	} = useSummaries({
		size: 20,
		sort: ["createdAt,desc"],
	});

	const summaries = summariesPage?.content || [];

	if (isLoading) {
		return (
			<Card>
				<CardHeader>
					<div className="flex items-center gap-2">
						<Calendar className="h-5 w-5" />
						<CardTitle className="text-lg">Timeline</CardTitle>
					</div>
					<CardDescription>
						Chronological view of generated summaries
					</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="space-y-4">
						{Array.from(
							{ length: 5 },
							(_, i) => `timeline-skeleton-${i + 1}`,
						).map((key) => (
							<div className="flex gap-4" key={key}>
								<div className="flex flex-col items-center">
									<div className="h-3 w-3 bg-slate-200 rounded-full animate-pulse" />
									<div className="w-px h-16 bg-slate-200 animate-pulse" />
								</div>
								<div className="flex-1 pb-4">
									<div className="h-4 w-1/3 bg-slate-200 rounded animate-pulse mb-2" />
									<div className="h-3 w-1/2 bg-slate-100 rounded animate-pulse mb-1" />
									<div className="h-3 w-2/3 bg-slate-100 rounded animate-pulse" />
								</div>
							</div>
						))}
					</div>
				</CardContent>
			</Card>
		);
	}

	if (error) {
		return (
			<Card>
				<CardHeader>
					<div className="flex items-center gap-2">
						<Calendar className="h-5 w-5" />
						<CardTitle className="text-lg">Timeline</CardTitle>
					</div>
				</CardHeader>
				<CardContent>
					<div className="text-center py-8">
						<Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
						<p className="text-muted-foreground">Failed to load timeline</p>
					</div>
				</CardContent>
			</Card>
		);
	}

	// Group summaries by week for better timeline organization
	const groupedSummaries = summaries.reduce(
		(acc, summary) => {
			const week = summary.week || "Unknown";
			if (!acc[week]) {
				acc[week] = [];
			}
			acc[week] = [...acc[week], summary];
			return acc;
		},
		{} as Record<string, Array<(typeof summaries)[0]>>,
	);

	return (
		<Card>
			<CardHeader>
				<div className="flex items-center gap-2">
					<Calendar className="h-5 w-5" />
					<CardTitle className="text-lg">Timeline</CardTitle>
				</div>
				<CardDescription>
					Chronological view of generated summaries
				</CardDescription>
			</CardHeader>
			<CardContent>
				{Object.keys(groupedSummaries).length > 0 ? (
					<div className="space-y-6">
						{Object.entries(groupedSummaries)
							.sort(([weekA], [weekB]) => weekB.localeCompare(weekA))
							.map(([week, weekSummaries]) => (
								<div key={week} className="space-y-4">
									<div className="flex items-center gap-2">
										<div className="h-px flex-1 bg-slate-200" />
										<span className="text-sm font-medium text-muted-foreground px-2">
											Week {week}
										</span>
										<div className="h-px flex-1 bg-slate-200" />
									</div>
									<div className="space-y-3">
										{weekSummaries.map((summary, index) => (
											<div key={summary.id} className="flex gap-4">
												<div className="flex flex-col items-center">
													<div
														className={`h-3 w-3 rounded-full ${
															index === 0 ? "bg-blue-500" : "bg-slate-300"
														}`}
													/>
													{index < weekSummaries.length - 1 && (
														<div className="w-px h-16 bg-slate-200" />
													)}
												</div>
												<div className="flex-1 pb-4">
													<Link
														href={`/summary/${summary.id}`}
														className="block hover:bg-slate-50 p-3 rounded-lg transition-colors border"
													>
														<div className="flex items-center justify-between mb-2">
															<h4 className="font-medium text-sm">
																{summary.username}
															</h4>
															<span className="text-xs text-muted-foreground">
																{summary.createdAt
																	? new Date(
																			summary.createdAt,
																		).toLocaleDateString(undefined, {
																			month: "short",
																			day: "numeric",
																			hour: "2-digit",
																			minute: "2-digit",
																		})
																	: "Unknown date"}
															</span>
														</div>
														<p className="text-xs text-muted-foreground mb-2">
															{summary.overview
																? `${summary.overview.substring(0, 120)}...`
																: "No summary available"}
														</p>
														<div className="flex items-center gap-2 text-xs">
															<span className="text-blue-600">
																{summary.totalContributions || 0} contributions
															</span>
															{summary.repositoryName && (
																<>
																	<span>•</span>
																	<span className="text-muted-foreground truncate max-w-32">
																		{summary.repositoryName}
																	</span>
																</>
															)}
														</div>
													</Link>
												</div>
											</div>
										))}
									</div>
								</div>
							))}
					</div>
				) : (
					<div className="text-center py-8">
						<Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
						<p className="text-muted-foreground">No summaries in timeline</p>
						<p className="text-xs text-muted-foreground mt-1">
							Generated summaries will appear here chronologically
						</p>
					</div>
				)}
			</CardContent>
		</Card>
	);
}

function QuickActions() {
	const generateSummary = useGenerateSummary();

	const getCurrentWeek = () => {
		const now = new Date();
		const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()));
		const year = startOfWeek.getFullYear();
		const weekNum = Math.ceil(
			(startOfWeek.getTime() - new Date(year, 0, 1).getTime()) /
				(7 * 24 * 60 * 60 * 1000),
		);
		return `${year}-W${weekNum.toString().padStart(2, "0")}`;
	};

	const handleGenerateWeeklySummary = async () => {
		try {
			// For demo purposes, using placeholder values
			// In a real implementation, these would come from user context or repository selection
			await generateSummary.mutateAsync({
				owner: "team",
				repo: "promptheus",
				username: "developer", // This should come from user context
				week: getCurrentWeek(),
			});

			toast({
				title: "Summary generation started",
				description:
					"Your weekly summary is being generated in the background.",
			});
		} catch (error) {
			console.error("Failed to generate weekly summary:", error);
			toast({
				title: "Failed to generate summary",
				description:
					"There was an error generating your weekly summary. Please try again.",
				variant: "destructive",
			});
		}
	};

	return (
		<Card>
			<CardHeader>
				<CardTitle className="text-lg">Quick Actions</CardTitle>
			</CardHeader>
			<CardContent className="space-y-3">
				<Button
					className="w-full justify-start"
					variant="outline"
					onClick={handleGenerateWeeklySummary}
					disabled={generateSummary.isPending}
				>
					{generateSummary.isPending ? (
						<Loader2 className="h-4 w-4 mr-2 animate-spin" />
					) : (
						<Clock className="h-4 w-4 mr-2" />
					)}
					Generate This Week's Summary
				</Button>
				<Button className="w-full justify-start" variant="outline" disabled>
					<Users className="h-4 w-4 mr-2" />
					Team Performance Report
				</Button>
				<Button className="w-full justify-start" variant="outline" disabled>
					<FileText className="h-4 w-4 mr-2" />
					Export All Summaries
				</Button>
				<Button className="w-full justify-start" variant="outline" disabled>
					<Calendar className="h-4 w-4 mr-2" />
					Schedule Auto-Summary
				</Button>
			</CardContent>
		</Card>
	);
}

export default function WeeklySummaryPage() {
	const { userId } = useUser();

	// Show not authenticated state if no userId
	if (!userId) {
		return (
			<div className="min-h-screen flex items-center justify-center bg-gray-50">
				<div className="max-w-md w-full text-center space-y-6">
					<div>
						<h2 className="text-2xl font-bold text-gray-900">
							Authentication Required
						</h2>
						<p className="mt-2 text-sm text-gray-600">
							Please log in to access the weekly summary builder
						</p>
					</div>
					<div className="space-y-4">
						<Button
							className="w-full"
							onClick={() => {
								window.location.href = "/login";
							}}
						>
							Go to Login
						</Button>
					</div>
				</div>
			</div>
		);
	}

	return (
		<>
			<header className="border-b bg-white">
				<div className="container mx-auto px-4 py-4">
					<div className="flex items-center gap-2">
						<Calendar className="h-6 w-6" />
						<h1 className="text-2xl font-bold">Weekly Summary Builder</h1>
					</div>
					<p className="text-slate-600">
						Create comprehensive weekly reports from your team's GitHub activity
					</p>
				</div>
			</header>

			<main className="container mx-auto px-4 py-8 max-w-6xl">
				<div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
					{/* Main Content - Summary Builder */}
					<div className="xl:col-span-2">
						<WeeklySummaryServer userId={userId} />
					</div>

					{/* Timeline - Recent Summaries */}
					<div className="xl:col-span-1">
						<SummariesTimeline />
					</div>

					{/* Sidebar - Actions and Quick Access */}
					<div className="xl:col-span-1 space-y-6">
						<Suspense
							fallback={
								<Card>
									<CardHeader>
										<div className="h-5 w-24 bg-slate-200 rounded animate-pulse" />
									</CardHeader>
									<CardContent className="space-y-3">
										<div className="h-9 bg-slate-100 rounded animate-pulse" />
										<div className="h-9 bg-slate-100 rounded animate-pulse" />
										<div className="h-9 bg-slate-100 rounded animate-pulse" />
										<div className="h-9 bg-slate-100 rounded animate-pulse" />
									</CardContent>
								</Card>
							}
						>
							<QuickActions />
						</Suspense>

						<Card>
							<CardHeader>
								<CardTitle className="text-lg">Summary Templates</CardTitle>
								<CardDescription>
									Choose from pre-built templates
								</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-3">
									<div className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
										<p className="font-medium text-sm">Executive Summary</p>
										<p className="text-xs text-muted-foreground">
											High-level overview for leadership
										</p>
									</div>
									<div className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
										<p className="font-medium text-sm">Technical Report</p>
										<p className="text-xs text-muted-foreground">
											Detailed technical progress
										</p>
									</div>
									<div className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
										<p className="font-medium text-sm">Team Standup</p>
										<p className="text-xs text-muted-foreground">
											Quick team update format
										</p>
									</div>
								</div>
							</CardContent>
						</Card>

						<Suspense
							fallback={
								<Card>
									<CardHeader>
										<div className="flex items-center gap-2">
											<FileText className="h-5 w-5" />
											<div className="h-5 w-32 bg-slate-200 rounded animate-pulse" />
										</div>
									</CardHeader>
									<CardContent>
										<div className="space-y-3">
											{/* biome-ignore-start lint/suspicious/noArrayIndexKey: skeletons are static */}
											{Array.from({ length: 3 }).map((_, i) => (
												<div
													className="flex items-center gap-3 p-2 border rounded"
													key={i}
												>
													<div className="h-8 w-8 bg-slate-200 rounded animate-pulse" />
													<div className="flex-1">
														<div className="h-4 w-2/3 bg-slate-200 rounded animate-pulse mb-1" />
														<div className="h-3 w-1/2 bg-slate-100 rounded animate-pulse" />
													</div>
												</div>
											))}
											{/* biome-ignore-end lint/suspicious/noArrayIndexKey: skeletons are static */}
										</div>
									</CardContent>
								</Card>
							}
						>
							<RecentSummaries />
						</Suspense>
					</div>
				</div>
			</main>
		</>
	);
}
