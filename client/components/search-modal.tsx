"use client";

import { format } from "date-fns";
import {
	AlertCircle,
	AlertTriangle,
	CalendarIcon,
	ExternalLink,
	Filter,
	GitCommit,
	GitPullRequest,
	Loader2,
	MessageSquare,
	Search,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
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
import { useSearch } from "@/lib/api";
import type {
	SearchFilters,
	SearchParams,
	SearchResult,
} from "@/lib/api/types";
import { SearchResultsLoading } from "./search-results-loading";

interface SearchModalProps {
	isOpen: boolean;
	onClose: () => void;
}

const contributionTypeIcons = {
	comment: MessageSquare,
	commit: GitCommit,
	issue: AlertCircle,
	pr: GitPullRequest,
};

const contributionTypeLabels = {
	comment: "Comments",
	commit: "Commits",
	issue: "Issues",
	pr: "Pull Requests",
};

const contributionTypeColors = {
	comment: "bg-purple-100 text-purple-800",
	commit: "bg-blue-100 text-blue-800",
	issue: "bg-red-100 text-red-800",
	pr: "bg-green-100 text-green-800",
};

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
	const [query, setQuery] = useState("");
	const [searchParams, setSearchParams] = useState<SearchParams>({
		authors: [],
		filterContributionType: ["commit", "pr", "issue", "comment"],
		query: "",
		repositories: [],
	});
	const [showFilters, setShowFilters] = useState(false);
	const [filters, setFilters] = useState<SearchFilters>({
		authors: [],
		contributionTypes: ["commit", "pr", "issue", "comment"],
		dateFrom: undefined,
		dateTo: undefined,
		repositories: [],
	});

	// Use TanStack Query for search
	const {
		data: searchResponse,
		isLoading,
		error,
		refetch,
	} = useSearch(searchParams, !!searchParams.query);

	const results = searchResponse?.results || [];

	// Mock data for repositories and authors
	const availableRepositories = [
		"auth-service",
		"api-backend",
		"job-processor",
		"api-gateway",
		"frontend-app",
		"mobile-app",
	];

	const availableAuthors = [
		"john.doe",
		"jane.smith",
		"mike.wilson",
		"sarah.johnson",
		"alex.brown",
		"lisa.davis",
	];

	const handleSearch = () => {
		if (!query.trim()) {
			setSearchParams((prev) => ({ ...prev, query: "" }));
			return;
		}

		setSearchParams({
			authors: filters.authors,
			dateFrom: filters.dateFrom?.toISOString(),
			dateTo: filters.dateTo?.toISOString(),
			filterContributionType: filters.contributionTypes,
			query: query.trim(),
			repositories: filters.repositories,
		});
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === "Enter") {
			handleSearch();
		}
	};

	const toggleContributionType = (type: string) => {
		setFilters((prev) => ({
			...prev,
			contributionTypes: prev.contributionTypes.includes(type)
				? prev.contributionTypes.filter((t) => t !== type)
				: [...prev.contributionTypes, type],
		}));
	};

	const toggleRepository = (repo: string) => {
		setFilters((prev) => ({
			...prev,
			repositories: prev.repositories.includes(repo)
				? prev.repositories.filter((r) => r !== repo)
				: [...prev.repositories, repo],
		}));
	};

	const toggleAuthor = (author: string) => {
		setFilters((prev) => ({
			...prev,
			authors: prev.authors.includes(author)
				? prev.authors.filter((a) => a !== author)
				: [...prev.authors, author],
		}));
	};

	const clearFilters = () => {
		setFilters({
			authors: [],
			contributionTypes: ["commit", "pr", "issue", "comment"],
			dateFrom: undefined,
			dateTo: undefined,
			repositories: [],
		});
		// Also clear search results
		setSearchParams((prev) => ({
			...prev,
			authors: [],
			dateFrom: undefined,
			dateTo: undefined,
			filterContributionType: ["commit", "pr", "issue", "comment"],
			repositories: [],
		}));
	};

	const getTypeIcon = (type: SearchResult["type"]) => {
		const Icon = contributionTypeIcons[type];
		return <Icon className="h-4 w-4" />;
	};

	// Reset state when modal closes
	useEffect(() => {
		if (!isOpen) {
			setQuery("");
			setShowFilters(false);
		}
	}, [isOpen]);

	return (
		<Dialog onOpenChange={onClose} open={isOpen}>
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
								onKeyPress={handleKeyPress}
								placeholder="Search commits, PRs, issues, comments..."
								value={query}
							/>
						</div>
						<Button disabled={isLoading} onClick={handleSearch}>
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
								<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
									{/* Contribution Types */}
									<div>
										<Label className="text-sm font-medium mb-2 block">
											Contribution Types
										</Label>
										<div className="space-y-2">
											{Object.entries(contributionTypeLabels).map(
												([type, label]) => (
													<div
														className="flex items-center space-x-2"
														key={type}
													>
														<Checkbox
															checked={filters.contributionTypes.includes(type)}
															id={type}
															onCheckedChange={() =>
																toggleContributionType(type)
															}
														/>
														<Label className="text-sm" htmlFor={type}>
															{label}
														</Label>
													</div>
												),
											)}
										</div>
									</div>

									{/* Repositories */}
									<div>
										<Label className="text-sm font-medium mb-2 block">
											Repositories
										</Label>
										<ScrollArea className="h-32">
											<div className="space-y-2">
												{availableRepositories.map((repo) => (
													<div
														className="flex items-center space-x-2"
														key={repo}
													>
														<Checkbox
															checked={filters.repositories.includes(repo)}
															id={repo}
															onCheckedChange={() => toggleRepository(repo)}
														/>
														<Label className="text-sm" htmlFor={repo}>
															{repo}
														</Label>
													</div>
												))}
											</div>
										</ScrollArea>
									</div>

									{/* Authors */}
									<div>
										<Label className="text-sm font-medium mb-2 block">
											Authors
										</Label>
										<ScrollArea className="h-32">
											<div className="space-y-2">
												{availableAuthors.map((author) => (
													<div
														className="flex items-center space-x-2"
														key={author}
													>
														<Checkbox
															checked={filters.authors.includes(author)}
															id={author}
															onCheckedChange={() => toggleAuthor(author)}
														/>
														<Label className="text-sm" htmlFor={author}>
															{author}
														</Label>
													</div>
												))}
											</div>
										</ScrollArea>
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
														initialFocus
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
										{filters.repositories.length > 0 && (
											<Badge variant="secondary">
												{filters.repositories.length} repo
												{filters.repositories.length > 1 ? "s" : ""}
											</Badge>
										)}
										{filters.authors.length > 0 && (
											<Badge variant="secondary">
												{filters.authors.length} author
												{filters.authors.length > 1 ? "s" : ""}
											</Badge>
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
								{results.map((result) => (
									<Card
										className="hover:bg-muted/50 transition-colors"
										key={result.id}
									>
										<CardContent className="p-4">
											<div className="flex items-start justify-between gap-4">
												<div className="flex-1 min-w-0">
													<div className="flex items-center gap-2 mb-2">
														<Badge
															className={`text-xs ${contributionTypeColors[result.type]}`}
														>
															{getTypeIcon(result.type)}
															<span className="ml-1">
																{contributionTypeLabels[result.type]}
															</span>
														</Badge>
														<Badge variant="outline">{result.repository}</Badge>
														<span className="text-xs text-muted-foreground">
															{Math.round(result.relevanceScore * 100)}% match
														</span>
													</div>
													<h3 className="font-medium text-sm mb-1 line-clamp-2">
														{result.title}
													</h3>
													<p className="text-xs text-muted-foreground mb-2 line-clamp-2">
														{result.description}
													</p>
													<div className="flex items-center gap-4 text-xs text-muted-foreground">
														<span>by {result.author}</span>
														<span>
															{new Date(result.date).toLocaleDateString()}
														</span>
													</div>
												</div>
												<Button asChild size="sm" variant="ghost">
													<a
														href={result.url}
														rel="noopener noreferrer"
														target="_blank"
													>
														<ExternalLink className="h-4 w-4" />
													</a>
												</Button>
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
