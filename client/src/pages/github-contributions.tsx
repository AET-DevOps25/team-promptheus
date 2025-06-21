"use client";

import { useState, useEffect } from "react";
import {
	Calendar,
	Clock,
	Code,
	GitCommit,
	GitPullRequest,
	MessageSquare,
	ChevronLeft,
	ChevronRight,
	Loader2,
	AlertCircle,
	Github,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// Helper function to get start and end of a week
const getWeekBounds = (date: Date) => {
	const day = date.getDay();
	const diff = date.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
	const monday = new Date(date);
	monday.setDate(diff);
	monday.setHours(0, 0, 0, 0);

	const sunday = new Date(monday);
	sunday.setDate(monday.getDate() + 6);
	sunday.setHours(23, 59, 59, 999);

	return { start: monday, end: sunday };
};

export default function GitHubContributions() {
	const today = new Date();
	const [currentWeek, setCurrentWeek] = useState(getWeekBounds(today));
	const [selectedContributions, setSelectedContributions] = useState<string[]>(
		[],
	);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [userData, setUserData] = useState<GitHubUser | null>(null);
	const [contributions, setContributions] = useState<GitHubContribution[]>([]);
	const [selectedRepo, setSelectedRepo] = useState<string | null>(null);

	// Check if a date is in the current week
	const isCurrentWeek = (dateString: string) => {
		const date = new Date(dateString);
		return date >= currentWeek.start && date <= currentWeek.end;
	};

	// Check if the selected week is the current week
	const isSelectedWeekCurrentWeek = () => {
		const todayBounds = getWeekBounds(today);
		return currentWeek.start.getTime() === todayBounds.start.getTime();
	};

	// Filter contributions for the current week and selected repo
	const weekContributions = contributions.filter((contribution) => {
		const date = new Date(contribution.date);
		const matchesWeek = date >= currentWeek.start && date <= currentWeek.end;
		const matchesRepo = selectedRepo
			? contribution.repoFullName === selectedRepo
			: true;
		return matchesWeek && matchesRepo;
	});

	// Get unique repositories from contributions
	const uniqueRepos = [
		...new Set(contributions.map((c) => c.repoFullName)),
	].sort();

	// Toggle selection of a contribution
	const toggleContribution = (id: string) => {
		if (!isSelectedWeekCurrentWeek()) return; // Only allow selection in current week
		setSelectedContributions((prev) =>
			prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
		);
	};

	// Select all contributions for the current week
	const selectAll = () => {
		if (!isSelectedWeekCurrentWeek()) return; // Only allow selection in current week
		setSelectedContributions(weekContributions.map((item) => item.id));
	};

	// Deselect all contributions
	const deselectAll = () => {
		if (!isSelectedWeekCurrentWeek()) return; // Only allow selection in current week
		setSelectedContributions([]);
	};

	// Navigate to previous week
	const goToPreviousWeek = () => {
		setCurrentWeek((prev) => {
			const newStart = new Date(prev.start);
			newStart.setDate(newStart.getDate() - 7);
			const newEnd = new Date(prev.end);
			newEnd.setDate(newEnd.getDate() - 7);
			return { start: newStart, end: newEnd };
		});
	};

	// Navigate to next week
	const goToNextWeek = () => {
		const nextWeekStart = new Date(currentWeek.start);
		nextWeekStart.setDate(nextWeekStart.getDate() + 7);

		// Don't allow navigating to future weeks
		if (nextWeekStart > today) return;

		setCurrentWeek((prev) => {
			const newStart = new Date(prev.start);
			newStart.setDate(newStart.getDate() + 7);
			const newEnd = new Date(prev.end);
			newEnd.setDate(newEnd.getDate() + 7);
			return { start: newStart, end: newEnd };
		});
	};

	// Format date range for display
	const formatDateRange = () => {
		const options: Intl.DateTimeFormatOptions = {
			month: "short",
			day: "numeric",
			year: "numeric",
		};
		const startStr = currentWeek.start.toLocaleDateString("en-US", options);
		const endStr = currentWeek.end.toLocaleDateString("en-US", options);
		return `${startStr} - ${endStr}`;
	};

	// Get icon based on contribution type
	const getContributionIcon = (type: string) => {
		switch (type) {
			case "commit":
				return <GitCommit className="h-4 w-4" />;
			case "issue":
				return <MessageSquare className="h-4 w-4" />;
			case "pull_request":
				return <GitPullRequest className="h-4 w-4" />;
			default:
				return <Code className="h-4 w-4" />;
		}
	};

	// Format date to readable string
	const formatDate = (dateString: string) => {
		const date = new Date(dateString);
		return date.toLocaleDateString("en-US", {
			month: "short",
			day: "numeric",
			year: "numeric",
		});
	};

	// Fetch contributions when week changes
	useEffect(() => {
		fetchContributions();
	}, [currentWeek]);

	// Fetch contributions
	const fetchContributions = async () => {
		setIsLoading(true);
		setError(null);

		try {
			/*
      const data = await fetchGitHubContributions("alinkcode", currentWeek.start, currentWeek.end)
      setUserData(data.user)
      setContributions(data.contributions)
       */
			throw "fetchGitHubContributions is only a stub";
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Failed to fetch GitHub data",
			);
		} finally {
			setIsLoading(false);
		}
	};

	// Export selected contributions
	const exportContributions = () => {
		const selectedItems = contributions.filter((c) =>
			selectedContributions.includes(c.id),
		);
		const exportData = {
			user: userData?.login,
			week: formatDateRange(),
			contributions: selectedItems.map((c) => ({
				type: c.type,
				repo: c.repoFullName,
				title: c.title,
				date: c.date,
				url: c.url,
			})),
		};

		const dataStr = JSON.stringify(exportData, null, 2);
		const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;

		const exportFileDefaultName = `github-contributions-${userData?.login}-${currentWeek.start.toISOString().split("T")[0]}.json`;

		const linkElement = document.createElement("a");
		linkElement.setAttribute("href", dataUri);
		linkElement.setAttribute("download", exportFileDefaultName);
		linkElement.click();
	};

	return (
		<Card className="w-full max-w-4xl mx-auto">
			<CardHeader>
				<div className="flex items-center justify-between">
					<CardTitle className="flex items-center gap-2">
						<Github className="h-5 w-5" />
						GitHub Contributions
					</CardTitle>
					{userData && (
						<div className="flex items-center gap-3">
							{selectedRepo && (
								<div className="text-sm text-muted-foreground">
									Repository:
									<Badge variant="outline" className="ml-2">
										{selectedRepo}
									</Badge>
									<Button
										variant="ghost"
										size="sm"
										className="h-6 ml-1 px-2"
										onClick={() => setSelectedRepo(null)}
									>
										Clear
									</Button>
								</div>
							)}
							<div className="flex items-center gap-2">
								<Avatar className="h-8 w-8">
									<AvatarImage
										src={userData.avatar_url || "/placeholder.svg"}
										alt={userData.login}
									/>
									<AvatarFallback>
										{userData.login.substring(0, 2).toUpperCase()}
									</AvatarFallback>
								</Avatar>
								<span className="font-medium">{userData.login}</span>
							</div>
						</div>
					)}
				</div>
				<CardDescription>
					View and select your GitHub contributions by week
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-6">
				<div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
					<div className="flex items-center gap-2">
						<Button variant="outline" size="icon" onClick={goToPreviousWeek}>
							<ChevronLeft className="h-4 w-4" />
						</Button>
						<div className="flex items-center gap-2">
							<Calendar className="h-4 w-4 text-muted-foreground" />
							<span className="font-medium">{formatDateRange()}</span>
						</div>
						<Button
							variant="outline"
							size="icon"
							onClick={goToNextWeek}
							disabled={isSelectedWeekCurrentWeek()}
						>
							<ChevronRight className="h-4 w-4" />
						</Button>
					</div>
					<div className="flex gap-2">
						{uniqueRepos.length > 0 && !selectedRepo && (
							<select
								className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors"
								onChange={(e) => setSelectedRepo(e.target.value)}
								value=""
							>
								<option value="">Filter by repository</option>
								{uniqueRepos.map((repo) => (
									<option key={repo} value={repo}>
										{repo}
									</option>
								))}
							</select>
						)}
						{isSelectedWeekCurrentWeek() && (
							<>
								<Button variant="outline" size="sm" onClick={selectAll}>
									Select All
								</Button>
								<Button variant="outline" size="sm" onClick={deselectAll}>
									Deselect All
								</Button>
							</>
						)}
						{!isSelectedWeekCurrentWeek() && (
							<Badge variant="secondary">View Only (Previous Week)</Badge>
						)}
					</div>
				</div>

				{isLoading ? (
					<div className="flex justify-center items-center py-12">
						<Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
						<span className="ml-2 text-muted-foreground">
							Loading contributions...
						</span>
					</div>
				) : error ? (
					<Alert variant="destructive">
						<AlertCircle className="h-4 w-4" />
						<AlertTitle>Error</AlertTitle>
						<AlertDescription>{error}</AlertDescription>
					</Alert>
				) : (
					<div className="border rounded-md">
						<div className="grid grid-cols-[25px_1fr] sm:grid-cols-[25px_1fr_200px] items-center gap-4 p-4 border-b bg-muted/50">
							<span></span>
							<span className="font-medium">Contribution</span>
							<span className="hidden sm:block font-medium">Date</span>
						</div>

						{weekContributions.length === 0 ? (
							<div className="p-8 text-center text-muted-foreground">
								No contributions found for this week
							</div>
						) : (
							<div className="divide-y">
								{weekContributions.map((contribution) => (
									<div
										key={contribution.id}
										className="grid grid-cols-[25px_1fr] sm:grid-cols-[25px_1fr_200px] items-center gap-4 p-4 hover:bg-muted/50 transition-colors"
									>
										<Checkbox
											id={`contribution-${contribution.id}`}
											checked={selectedContributions.includes(contribution.id)}
											onCheckedChange={() =>
												toggleContribution(contribution.id)
											}
											disabled={!isSelectedWeekCurrentWeek()}
										/>
										<div className="space-y-1">
											<div className="flex items-center gap-2">
												<Badge
													variant="outline"
													className="flex items-center gap-1"
												>
													{getContributionIcon(contribution.type)}
													<span className="capitalize">
														{contribution.type.replace("_", " ")}
													</span>
												</Badge>
												<span className="text-sm text-muted-foreground">
													{contribution.repo}
												</span>
											</div>

											<Button asChild>
												<a
													href={contribution.url}
													target="_blank"
													rel="noopener noreferrer"
													className="hover:underline"
												>
													{contribution.title}
												</a>
											</Button>

											{/* <Label
                        htmlFor={`contribution-${contribution.id}`}
                        className={`font-medium ${isSelectedWeekCurrentWeek() ? "cursor-pointer hover:text-primary" : ""}`}
                      >
                        <a
                          href={contribution.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline"
                        >
                          {contribution.title}
                        </a>
                      </Label> */}
										</div>
										<div className="hidden sm:flex items-center gap-1 text-sm text-muted-foreground">
											<Clock className="h-3 w-3" />
											{formatDate(contribution.date)}
										</div>
										<div className="sm:hidden text-xs text-muted-foreground mt-1">
											{formatDate(contribution.date)}
										</div>
									</div>
								))}
							</div>
						)}
					</div>
				)}
			</CardContent>
			<CardFooter className="flex justify-between">
				<div className="text-sm text-muted-foreground">
					{isSelectedWeekCurrentWeek()
						? `${selectedContributions.length} of ${weekContributions.length} contributions selected`
						: "Selection disabled for previous weeks"}
				</div>
				<Button
					disabled={
						!isSelectedWeekCurrentWeek() || selectedContributions.length === 0
					}
					onClick={exportContributions}
				>
					Export Selected
				</Button>
			</CardFooter>
		</Card>
	);
}
