"use client";

import { Calendar, Download, FileText, Loader2, Send } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { Suspense, useId, useState } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { useUser } from "@/contexts/user-context";
import { toast } from "@/hooks/use-toast";
import { useContributions } from "@/lib/api/contributions";
import { useGitRepoInformation } from "@/lib/api/server";
import { useGenerateSummary, useSummaries } from "@/lib/api/summary";
import type { components } from "@/lib/api/types/contribution";

type ContributionDto = components["schemas"]["ContributionDto"];

function WeeklySummaryForm({ userId }: { userId: string }) {
	const router = useRouter();
	const [selectedWeek, setSelectedWeek] = useState<Date | undefined>(
		new Date(),
	);
	const [selectedUser, setSelectedUser] = useState<string>("");
	const [isGenerating, setIsGenerating] = useState(false);

	// Generate unique IDs for form elements
	const weekSelectorId = useId();
	const userSelectId = useId();

	// Fetch repository information using the userId (usercode)
	const { data: repoInfo, isLoading: repoLoading } =
		useGitRepoInformation(userId);

	// Hook for generating summaries
	const generateSummary = useGenerateSummary();

	// Fetch contributions to get available users
	const { data: contributionsData, isLoading: contributionsLoading } =
		useContributions({
			pageable: {
				page: 0,
				size: 1000, // Get a large number to capture all unique users
			},
		});

	// Extract unique users from contributions data
	const availableUsers = React.useMemo(() => {
		if (!contributionsData?.content) return [];
		const contributions = contributionsData.content as ContributionDto[];
		const users = Array.from(new Set(contributions.map((c) => c.username)))
			.filter(Boolean)
			.sort();
		return users;
	}, [contributionsData]);

	// Extract repository name and owner/repo from repoLink
	const repositoryInfo = React.useMemo(() => {
		if (!repoInfo?.repoLink) return { name: "Loading...", owner: "", repo: "" };
		try {
			// Parse GitHub URL to get organization/repository
			const url = new URL(repoInfo.repoLink);
			const pathParts = url.pathname.split("/").filter(Boolean);
			if (pathParts.length >= 2) {
				const owner = pathParts[0];
				const repo = pathParts[1];
				return {
					name: `${owner}/${repo}`,
					owner,
					repo,
				};
			}
			return { name: repoInfo.repoLink, owner: "", repo: "" };
		} catch {
			return { name: repoInfo.repoLink, owner: "", repo: "" };
		}
	}, [repoInfo]);

	// Format date to week string (YYYY-WMM)
	const formatToWeek = (date: Date) => {
		const year = date.getFullYear();
		const startOfYear = new Date(year, 0, 1);
		const days = Math.floor(
			(date.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000),
		);
		const weekNumber = Math.ceil((days + startOfYear.getDay() + 1) / 7);
		return `${year}-W${weekNumber.toString().padStart(2, "0")}`;
	};

	const handleGenerateWeeklySummary = async () => {
		if (!selectedWeek || !selectedUser) {
			toast({
				title: "Missing selections",
				description: "Please select both a week and a user",
				variant: "destructive",
			});
			return;
		}

		if (!repositoryInfo.owner || !repositoryInfo.repo) {
			toast({
				title: "Repository information missing",
				description: "Unable to determine repository details",
				variant: "destructive",
			});
			return;
		}

		setIsGenerating(true);

		try {
			const week = formatToWeek(selectedWeek);

			// Make the actual API call to generate summary
			await generateSummary.mutateAsync({
				owner: repositoryInfo.owner,
				repo: repositoryInfo.repo,
				username: selectedUser,
				week: week,
			});

			toast({
				title: "Summary generation started!",
				description: `Generating weekly summary for ${selectedUser} in week ${week}. You'll be redirected to the dashboard where it will appear soon.`,
			});

			// Redirect to dashboard after brief delay
			setTimeout(() => {
				router.push("/dashboard");
			}, 1500);
		} catch (error) {
			console.error("Failed to generate summary:", error);
			toast({
				title: "Failed to generate summary",
				description:
					"There was an error generating your weekly summary. Please try again.",
				variant: "destructive",
			});
		} finally {
			setIsGenerating(false);
		}
	};

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<Calendar className="h-5 w-5" />
					Generate Weekly Summary
				</CardTitle>
				<CardDescription>
					Select a week and user to generate a comprehensive summary of their
					contributions
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-6">
				{/* Week Selection */}
				<div className="space-y-2">
					<Label htmlFor="week-selector" className="text-sm font-medium">
						Select Week
					</Label>
					<div className="border rounded-lg p-3">
						<div className="flex items-center justify-between mb-3">
							<div className="text-sm text-muted-foreground">
								Choose any week to generate a summary for
							</div>
							{selectedWeek && (
								<div className="text-sm font-medium text-blue-600">
									Week: {formatToWeek(selectedWeek)}
								</div>
							)}
						</div>
						<div className="flex justify-center">
							<div className="w-fit">
								<input
									id={weekSelectorId}
									type="week"
									value={
										selectedWeek
											? selectedWeek
													.toISOString()
													.slice(0, 10)
													.replace(/\d{2}$/, "01")
											: ""
									}
									onChange={(e) => {
										if (e.target.value) {
											const [year, week] = e.target.value.split("-W");
											const date = new Date(
												parseInt(year),
												0,
												1 + (parseInt(week) - 1) * 7,
											);
											setSelectedWeek(date);
										}
									}}
									className="w-full p-2 border rounded"
								/>
							</div>
						</div>
					</div>
				</div>

				{/* Repository Display (Read-only) */}
				<div className="space-y-2">
					<Label className="text-sm font-medium">Repository</Label>
					<div className="w-full p-3 border rounded-lg bg-slate-50 text-slate-700">
						{repoLoading ? (
							<div className="flex items-center gap-2">
								<Loader2 className="h-4 w-4 animate-spin" />
								Loading repository information...
							</div>
						) : (
							<div className="flex items-center gap-2">
								<FileText className="h-4 w-4 text-slate-500" />
								{repositoryInfo.name}
							</div>
						)}
					</div>
				</div>

				{/* User Selection */}
				<div className="space-y-2">
					<Label htmlFor={userSelectId} className="text-sm font-medium">
						Select Developer
					</Label>
					<Select value={selectedUser} onValueChange={setSelectedUser}>
						<SelectTrigger id={userSelectId}>
							<SelectValue
								placeholder={
									contributionsLoading
										? "Loading developers..."
										: "Choose a developer"
								}
							/>
						</SelectTrigger>
						<SelectContent>
							{contributionsLoading ? (
								<SelectItem value="loading" disabled>
									Loading developers...
								</SelectItem>
							) : availableUsers.length > 0 ? (
								availableUsers.map((user) => (
									<SelectItem key={user} value={user}>
										{user}
									</SelectItem>
								))
							) : (
								<SelectItem value="no-users" disabled>
									No developers found
								</SelectItem>
							)}
						</SelectContent>
					</Select>
				</div>

				{/* Generate Button */}
				<Button
					onClick={handleGenerateWeeklySummary}
					disabled={
						isGenerating ||
						!selectedWeek ||
						!selectedUser ||
						contributionsLoading ||
						repoLoading
					}
					className="w-full"
					size="lg"
				>
					{isGenerating ? (
						<>
							<Loader2 className="mr-2 h-4 w-4 animate-spin" />
							Generating Summary...
						</>
					) : (
						<>
							<Send className="mr-2 h-4 w-4" />
							Generate Weekly Summary
						</>
					)}
				</Button>

				{isGenerating && (
					<div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
						<p className="text-green-800 font-medium">
							✨ Generating weekly summary...
						</p>
						<p className="text-sm text-green-700 mt-1">
							This will take a moment and you'll be redirected to the dashboard!
						</p>
					</div>
				)}
			</CardContent>
		</Card>
	);
}

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
				<div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
					{/* Main Content - Summary Builder */}
					<div className="xl:col-span-2">
						<WeeklySummaryForm userId={userId} />
					</div>

					{/* Timeline - Recent Summaries */}
					<div className="xl:col-span-1 space-y-6">
						<SummariesTimeline />

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
