"use client";

import { format } from "date-fns";
import {
	AlertCircle,
	CalendarIcon,
	ExternalLink,
	Filter,
	GitCommit,
	GitPullRequest,
	Loader2,
	MessageSquare,
	Search,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent } from "@/components/ui/card";

import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useDebounce } from "@/hooks/use-debounce";
import type { useSearchParams } from "@/lib/api/search";
import { useSearch } from "@/lib/api/search";
import { SearchResultsLoading } from "./search-results-loading";

interface SearchModalProps {
	isOpen: boolean;
	onCloseAction: () => void;
	usercode: string;
}

interface SearchFilters {
	author: string | undefined;
	contributionType: string | undefined;
	dateFrom: Date | undefined;
	dateTo: Date | undefined;
	repository: string | undefined;
	week: string | undefined;
	user: string | undefined;
}

interface SearchResultItem {
	id?: string;
	type?: "commit" | "pr" | "issue" | "comment";
	title?: string;
	content?: string;
	description?: string;
	author?: string;
	date?: string;
	created_at_timestamp?: number;
	url?: string;
	repository?: string;
	relevanceScore?: number;
	[key: string]: unknown;
}

const contributionTypeIcons = {
	comment: MessageSquare,
	commit: GitCommit,
	issue: AlertCircle,
	pr: GitPullRequest,
} as const;

const contributionTypeLabels = {
	comment: "Comments",
	commit: "Commits",
	issue: "Issues",
	pr: "Pull Requests",
} as const;

const contributionTypeColors = {
	comment: "bg-purple-100 text-purple-800",
	commit: "bg-blue-100 text-blue-800",
	issue: "bg-red-100 text-red-800",
	pr: "bg-green-100 text-green-800",
} as const;

export function SearchModal({
	isOpen,
	onCloseAction,
	usercode,
}: SearchModalProps) {
	const [query, setQuery] = useState("");
	const [showFilters, setShowFilters] = useState(false);
	const [filters, setFilters] = useState<SearchFilters>({
		author: undefined,
		contributionType: undefined,
		dateFrom: undefined,
		dateTo: undefined,
		repository: undefined,
		user: undefined,
		week: undefined,
	});

	// Debounce the query to avoid excessive API calls
	const debouncedQuery = useDebounce(query, 50);

	// Create search params from debounced query and filters
	const searchParams: useSearchParams = {
		author: filters.author,
		contribution_type: filters.contributionType,
		created_at_timestamp:
			filters.dateFrom && filters.dateTo
				? `${Math.floor(filters.dateFrom.getTime() / 1000)} TO ${Math.floor(filters.dateTo.getTime() / 1000)}`
				: filters.dateFrom
					? `${Math.floor(filters.dateFrom.getTime() / 1000)} TO *`
					: filters.dateTo
						? `* TO ${Math.floor(filters.dateTo.getTime() / 1000)}`
						: undefined,
		query: debouncedQuery,
		repository: filters.repository,
		user: filters.user,
		week: filters.week,
	};

	// Use TanStack Query for search
	const {
		data: searchResponse,
		isLoading,
		error,
		refetch,
	} = useSearch(usercode, searchParams, !!debouncedQuery.trim());

	const results = searchResponse?.hits || [];

	const handleFilterChange = (
		key: keyof SearchFilters,
		value: string | undefined,
	) => {
		setFilters((prev) => ({
			...prev,
			[key]: value,
		}));
	};

	const clearFilters = () => {
		setFilters({
			author: undefined,
			contributionType: undefined,
			dateFrom: undefined,
			dateTo: undefined,
			repository: undefined,
			user: undefined,
			week: undefined,
		});
		// Search results will clear automatically when query is cleared
	};

	const getTypeIcon = (type: string) => {
		const Icon =
			contributionTypeIcons[type as keyof typeof contributionTypeIcons];
		return Icon ? <Icon className="h-4 w-4" /> : null;
	};

	// Reset state when modal closes
	useEffect(() => {
		if (!isOpen) {
			setQuery("");
			setShowFilters(false);
		}
	}, [isOpen]);

	return (
		<Dialog onOpenChange={onCloseAction} open={isOpen}>
			<DialogContent className="max-w-4xl max-h-[80vh] p-0">
				<DialogHeader className="p-6 pb-0">
					<DialogTitle className="flex items-center gap-2">
						<Search className="h-5 w-5" />
						Semantic Search
					</DialogTitle>
				</DialogHeader>

				<div className="px-6">
					{/* Search Input */}
					<div className="flex gap-2 mb-4">
						<div className="relative flex-1">
							<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
							<Input
								autoFocus
								className="pl-10"
								onChange={(e) => setQuery(e.target.value)}
								placeholder="Search commits, PRs, issues, comments..."
								value={query}
							/>
						</div>
						<Button disabled={isLoading}>
							{isLoading ? (
								<Loader2 className="h-4 w-4 animate-spin" />
							) : (
								"Search"
							)}
						</Button>
						<Button
							onClick={() => setShowFilters(!showFilters)}
							variant="outline"
						>
							<Filter className="h-4 w-4 mr-2" />
							Filters
						</Button>
					</div>

					{/* Filters Panel */}
					{showFilters && (
						<Card className="mb-4">
							<CardContent className="p-4">
								<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
									{/* Basic Filters */}
									<div>
										<Label className="text-sm font-medium mb-2 block">
											Author
										</Label>
										<Input
											className="mb-4"
											onChange={(e) =>
												handleFilterChange(
													"author",
													e.target.value || undefined,
												)
											}
											placeholder="Filter by author"
											value={filters.author || ""}
										/>

										<Label className="text-sm font-medium mb-2 block">
											Repository
										</Label>
										<Input
											className="mb-4"
											onChange={(e) =>
												handleFilterChange(
													"repository",
													e.target.value || undefined,
												)
											}
											placeholder="Filter by repository"
											value={filters.repository || ""}
										/>

										<Label className="text-sm font-medium mb-2 block">
											Contribution Type
										</Label>
										<Input
											className="mb-4"
											onChange={(e) =>
												handleFilterChange(
													"contributionType",
													e.target.value || undefined,
												)
											}
											placeholder="commit, pr, issue, comment"
											value={filters.contributionType || ""}
										/>

										<Label className="text-sm font-medium mb-2 block">
											Week
										</Label>
										<Input
											className="mb-4"
											onChange={(e) =>
												handleFilterChange("week", e.target.value || undefined)
											}
											placeholder="Filter by week"
											value={filters.week || ""}
										/>

										<Label className="text-sm font-medium mb-2 block">
											User
										</Label>
										<Input
											onChange={(e) =>
												handleFilterChange("user", e.target.value || undefined)
											}
											placeholder="Filter by user"
											value={filters.user || ""}
										/>
									</div>

									{/* Date Range */}
									<div>
										<Label className="text-sm font-medium mb-2 block">
											Date Range
										</Label>
										<div className="space-y-2">
											<Popover>
												<PopoverTrigger asChild>
													<Button
														className="w-full justify-start text-left font-normal"
														variant="outline"
													>
														<CalendarIcon className="mr-2 h-4 w-4" />
														{filters.dateFrom
															? format(filters.dateFrom, "PPP")
															: "From date"}
													</Button>
												</PopoverTrigger>
												<PopoverContent className="w-auto p-0">
													<Calendar
														initialFocus
														mode="single"
														onSelect={(date) =>
															setFilters((prev) => ({
																...prev,
																dateFrom: date,
															}))
														}
														selected={filters.dateFrom}
													/>
												</PopoverContent>
											</Popover>
											<Popover>
												<PopoverTrigger asChild>
													<Button
														className="w-full justify-start text-left font-normal"
														variant="outline"
													>
														<CalendarIcon className="mr-2 h-4 w-4" />
														{filters.dateTo
															? format(filters.dateTo, "PPP")
															: "To date"}
													</Button>
												</PopoverTrigger>
												<PopoverContent className="w-auto p-0">
													<Calendar
														autoFocus
														mode="single"
														onSelect={(date) =>
															setFilters((prev) => ({ ...prev, dateTo: date }))
														}
														selected={filters.dateTo}
													/>
												</PopoverContent>
											</Popover>
										</div>
									</div>
								</div>

								<Separator className="my-4" />
								<div className="flex justify-between items-center">
									<div className="flex gap-2 flex-wrap">
										{filters.repository && (
											<Badge variant="secondary">Repository filtered</Badge>
										)}
										{filters.author && (
											<Badge variant="secondary">Author filtered</Badge>
										)}
										{filters.contributionType && (
											<Badge variant="secondary">Type filtered</Badge>
										)}
										{filters.week && (
											<Badge variant="secondary">Week filtered</Badge>
										)}
										{filters.user && (
											<Badge variant="secondary">User filtered</Badge>
										)}
										{(filters.dateFrom || filters.dateTo) && (
											<Badge variant="secondary">Date filtered</Badge>
										)}
									</div>
									<Button onClick={clearFilters} size="sm" variant="ghost">
										Clear all
									</Button>
								</div>
							</CardContent>
						</Card>
					)}
				</div>

				{/* Results */}
				<ScrollArea className="flex-1 px-6 pb-6">
					<div className="space-y-4">
						{isLoading ? (
							<SearchResultsLoading />
						) : error ? (
							<div className="text-center py-8">
								<p className="text-red-600 mb-2">
									{error instanceof Error
										? error.message
										: "Search failed. Please try again."}
								</p>
								<Button onClick={() => refetch()} size="sm" variant="outline">
									Try Again
								</Button>
							</div>
						) : results.length > 0 ? (
							<div className="space-y-3">
								<div className="flex items-center justify-between">
									<p className="text-sm text-muted-foreground">
										{results.length} result{results.length !== 1 ? "s" : ""}{" "}
										found
										{searchResponse?.processingTimeMs && (
											<span className="ml-2">
												({searchResponse.processingTimeMs}ms)
											</span>
										)}
									</p>
									<Button
										className="text-xs"
										onClick={clearFilters}
										size="sm"
										variant="ghost"
									>
										Clear filters
									</Button>
								</div>
								{results.map((result: SearchResultItem, index: number) => (
									<Card
										className="hover:bg-muted/50 transition-colors"
										key={result.id || index}
									>
										<CardContent className="p-4">
											<div className="flex items-start justify-between gap-4">
												<div className="flex-1 min-w-0">
													<div className="flex items-center gap-2 mb-2">
														{result.type && (
															<Badge
																className={`text-xs ${contributionTypeColors[result.type] || "bg-gray-100 text-gray-800"}`}
															>
																{getTypeIcon(result.type)}
																<span className="ml-1">
																	{contributionTypeLabels[result.type] ||
																		result.type}
																</span>
															</Badge>
														)}
														{result.repository && (
															<Badge variant="outline">
																{result.repository}
															</Badge>
														)}
														{result.relevanceScore && (
															<span className="text-xs text-muted-foreground">
																{Math.round(result.relevanceScore * 100)}% match
															</span>
														)}
													</div>
													<h3 className="font-medium text-sm mb-1 line-clamp-2">
														{result.title || result.content || "No title"}
													</h3>
													{result.description && (
														<p className="text-xs text-muted-foreground mb-2 line-clamp-2">
															{result.description}
														</p>
													)}
													<div className="flex items-center gap-4 text-xs text-muted-foreground">
														{result.author && <span>by {result.author}</span>}
														{result.date && (
															<span>
																{new Date(result.date).toLocaleDateString()}
															</span>
														)}
														{result.created_at_timestamp && !result.date && (
															<span>
																{new Date(
																	result.created_at_timestamp * 1000,
																).toLocaleDateString()}
															</span>
														)}
													</div>
												</div>
												{result.url && (
													<Button asChild size="sm" variant="ghost">
														<a
															href={result.url}
															rel="noopener noreferrer"
															target="_blank"
														>
															<ExternalLink className="h-4 w-4" />
														</a>
													</Button>
												)}
											</div>
										</CardContent>
									</Card>
								))}
							</div>
						) : query && !isLoading ? (
							<div className="text-center py-8">
								<Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
								<p className="text-muted-foreground">
									No results found for "{query}"
								</p>
								<p className="text-sm text-muted-foreground mt-2">
									Try adjusting your search terms or filters
								</p>
							</div>
						) : (
							<div className="text-center py-8">
								<Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
								<p className="text-muted-foreground">
									Start typing to search across your repositories
								</p>
								<p className="text-sm text-muted-foreground mt-2">
									Search commits, pull requests, issues, and comments with
									AI-powered semantic understanding
								</p>
							</div>
						)}
					</div>
				</ScrollArea>
			</DialogContent>
		</Dialog>
	);
}

export default SearchModal;
