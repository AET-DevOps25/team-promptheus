"use client";

import { Calendar } from "lucide-react";
import Link from "next/link";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { useSummaries } from "@/lib/api/summary";

export function SummariesTimeline() {
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
							(_, i) => `summaries-timeline-skeleton-${i + 1}`,
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
