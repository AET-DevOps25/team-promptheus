/**
 * API services index - exports all API hooks and utilities
 */

// Re-export commonly used TanStack Query utilities
export {
	useInfiniteQuery,
	useMutation,
	useQuery,
	useQueryClient,
} from "@tanstack/react-query";
// Export API client
export { ApiClient, ApiError, apiClient } from "./client";

// Export service hooks
export * from "./qa";
export { SEARCH_KEYS, useSearch } from "./search";

// Export types (with explicit exports to avoid conflicts)
export type {
	ApiErrorResponse,
	ApiSuccessResponse,
	CreateQARequest,
	CreateQAResponse,
	QAItem,
	QAResponse,
	SearchFilters,
	SearchParams,
	SearchResponse,
	SearchResult,
	StatusUpdateRequest,
	VoteRequest,
	VoteResponse,
	WeeklySummariesResponse,
	WeeklySummary,
} from "./types";
export { QueryKeys } from "./types";
