"use client";

import {
	Bug,
	Calendar,
	Eye,
	FileText,
	GitCommit,
	GitPullRequest,
	Package,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useSummaries } from "@/lib/api";

function SummariesLoading() {
	return (
		<div className="container mx-auto px-4 py-8 max-w-6xl">
			<div className="space-y-6">
				{/* Header */}
				<div className="flex items-center gap-2 mb-6">
					<Skeleton className="h-8 w-8" />
					<Skeleton className="h-8 w-48" />
				</div>

				{/* Filters */}
				<div className="flex gap-4 mb-6">
					<Skeleton className="h-10 w-64" />
					<Skeleton className="h-10 w-48" />
				</div>

				{/* Table */}
				<Card>
					<CardHeader>
						<Skeleton className="h-6 w-32" />
					</CardHeader>
					<CardContent>
						<div className="space-y-4">
							{Array.from({ length: 8 }, () => crypto.randomUUID()).map(
								(uuid) => (
									<div
										className="flex items-center gap-4 p-4 border rounded-lg"
										key={uuid}
									>
										<Skeleton className="h-8 w-8" />
										<div className="flex-1">
											<Skeleton className="h-5 w-48 mb-2" />
											<Skeleton className="h-4 w-32" />
										</div>
										<div className="flex gap-2">
											<Skeleton className="h-6 w-12" />
											<Skeleton className="h-6 w-12" />
											<Skeleton className="h-6 w-12" />
											<Skeleton className="h-6 w-12" />
										</div>
										<Skeleton className="h-9 w-20" />
									</div>
								),
							)}
						</div>
					</CardContent>
				</Card>
			</div>
		</div>
	);
}

export default function SummariesPage() {
	const [weekFilter, setWeekFilter] = useState<string>("all");
	const [userFilter, setUserFilter] = useState<string>("");

	const {
		data: summaries,
		isLoading,
		error,
	} = useSummaries(
		weekFilter && weekFilter !== "all" ? { week: weekFilter } : undefined,
	);

	// Filter summaries by user if user filter is set
	const filteredSummaries =
		summaries?.filter(
			(summary) =>
				!userFilter ||
				summary.username?.toLowerCase().includes(userFilter.toLowerCase()),
		) || [];

	// Get unique weeks and users for filter options
	const availableWeeks = [
		...new Set(summaries?.map((s) => s.week).filter(Boolean)),
	]
		.sort()
		.reverse();
	const _availableUsers = [
		...new Set(summaries?.map((s) => s.username).filter(Boolean)),
	].sort();

	if (isLoading) {
		return <SummariesLoading />;
	}

	if (error) {
		return (
			<div className="container mx-auto px-4 py-8 max-w-6xl">
				<div className="text-center py-12">
					<h2 className="text-2xl font-bold text-gray-900 mb-2">
						Error Loading Summaries
					</h2>
					<p className="text-gray-600 mb-4">
						There was an error loading the summaries.
					</p>
					<Button onClick={() => window.location.reload()}>Retry</Button>
				</div>
			</div>
		);
	}

	return (
		<div className="container mx-auto px-4 py-8 max-w-6xl">
			<div className="space-y-6">
				{/* Header */}
				<div className="flex items-center gap-2 mb-6">
					<FileText className="h-8 w-8" />
					<h1 className="text-3xl font-bold">Summaries</h1>
				</div>

				{/* Filters */}
				<div className="flex gap-4 mb-6">
					<Input
						className="max-w-64"
						onChange={(e) => setUserFilter(e.target.value)}
						placeholder="Filter by user..."
						value={userFilter}
					/>
					<Select onValueChange={setWeekFilter} value={weekFilter}>
						<SelectTrigger className="w-48">
							<SelectValue placeholder="Filter by week" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All weeks</SelectItem>
							{availableWeeks.map((week) => (
								<SelectItem key={week} value={week || "unknown"}>
									{week}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
					{((weekFilter && weekFilter !== "all") || userFilter) && (
						<Button
							onClick={() => {
								setWeekFilter("all");
								setUserFilter("");
							}}
							variant="outline"
						>
							Clear Filters
						</Button>
					)}
				</div>

				{/* Summaries Table */}
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<FileText className="h-5 w-5" />
							Generated Summaries ({filteredSummaries.length})
						</CardTitle>
					</CardHeader>
					<CardContent>
						{filteredSummaries.length === 0 ? (
							<div className="text-center py-12">
								<FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
								<h3 className="text-lg font-semibold text-gray-900 mb-2">
									No summaries found
								</h3>
								<p className="text-gray-600">
									{(weekFilter && weekFilter !== "all") || userFilter
										? "No summaries match your current filters."
										: "No summaries have been generated yet."}
								</p>
							</div>
						) : (
							<div className="space-y-4">
								{filteredSummaries.map((summary) => (
									<div
										className="flex items-center gap-4 p-4 border rounded-lg hover:bg-slate-50 transition-colors"
										key={summary.id}
									>
										<div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
											<FileText className="h-5 w-5 text-blue-600" />
										</div>

										<div className="flex-1 min-w-0">
											<div className="flex items-center gap-2 mb-1">
												<p className="font-semibold text-lg truncate">
													{summary.username}'s Summary
												</p>
												<Badge variant="secondary">{summary.week}</Badge>
											</div>
											<div className="flex items-center gap-2 text-sm text-muted-foreground">
												<Calendar className="h-4 w-4" />
												<span>
													Generated on{" "}
													{summary.createdAt
														? new Date(summary.createdAt).toLocaleDateString()
														: "Unknown date"}
												</span>
											</div>
										</div>

										{/* Stats */}
										<div className="flex gap-4 text-sm">
											<div className="flex items-center gap-1">
												<GitCommit className="h-4 w-4 text-blue-600" />
												<span className="font-medium">
													{summary.commitsCount || 0}
												</span>
											</div>
											<div className="flex items-center gap-1">
												<GitPullRequest className="h-4 w-4 text-green-600" />
												<span className="font-medium">
													{summary.pullRequestsCount || 0}
												</span>
											</div>
											<div className="flex items-center gap-1">
												<Bug className="h-4 w-4 text-orange-600" />
												<span className="font-medium">
													{summary.issuesCount || 0}
												</span>
											</div>
											<div className="flex items-center gap-1">
												<Package className="h-4 w-4 text-purple-600" />
												<span className="font-medium">
													{summary.releasesCount || 0}
												</span>
											</div>
										</div>

										{/* Actions */}
										<div className="flex gap-2">
											<Button asChild size="sm">
												<Link href={`/summary/${summary.id}`}>
													<Eye className="h-4 w-4 mr-2" />
													View
												</Link>
											</Button>
										</div>
									</div>
								))}
							</div>
						)}
					</CardContent>
				</Card>
			</div>
		</div>
	);
}
