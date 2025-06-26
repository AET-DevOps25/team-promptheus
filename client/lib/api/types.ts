/**
 * TypeScript type definitions for API responses and data structures
 */

export interface QAItem {
	id: string;
	question: string;
	answer: string;
	author: string;
	timestamp: string;
	status: "pending" | "approved" | "rejected";
	upvotes: number;
	downvotes: number;
	repositories: string[];
	tags: string[];
}

export interface SearchResult {
	id: string;
	type: "commit" | "pr" | "issue" | "comment";
	title: string;
	description: string;
	repository: string;
	author: string;
	date: string;
	url: string;
	relevanceScore: number;
}

export interface SearchFilters {
	contributionTypes: string[];
	repositories: string[];
	authors: string[];
	dateFrom?: Date;
	dateTo?: Date;
}

export interface SearchParams {
	query: string;
	filterContributionType?: string[];
	repositories?: string[];
	authors?: string[];
	dateFrom?: string;
	dateTo?: string;
}

export interface SearchResponse {
	results: SearchResult[];
	total: number;
	query: string;
	filters: {
		contributionTypes: string[];
		repositories: string[];
		authors: string[];
		dateFrom?: string;
		dateTo?: string;
	};
}

export interface QAResponse {
	items: QAItem[];
	total: number;
}

export interface VoteRequest {
	type: "up" | "down";
}

export interface VoteResponse {
	upvotes: number;
	downvotes: number;
}

export interface StatusUpdateRequest {
	status: "approved" | "rejected";
}

export interface CreateQARequest {
	question: string;
}

export interface CreateQAResponse {
	item: QAItem;
}

export interface WeeklySummary {
	id: string;
	title: string;
	date: string;
	status: "draft" | "published";
	itemCount: number;
}

export interface WeeklySummariesResponse {
	summaries: WeeklySummary[];
	total: number;
}

// Generic API response wrapper
export interface ApiSuccessResponse<T> {
	data: T;
	success: true;
	message?: string;
}

export interface ApiErrorResponse {
	error: string;
	success: false;
	status?: number;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

// Query keys for TanStack Query
export const QueryKeys = {
	QA: "qa",
	QA_ITEM: "qa-item",
	SEARCH: "search",
	WEEKLY_SUMMARIES: "weekly-summaries",
} as const;
