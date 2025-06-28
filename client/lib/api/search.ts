/**
 * Search API service with TanStack Query hooks
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { components, operations } from "./types/search";

// Extract types from OpenAPI schema
type SearchResult = components["schemas"]["SearchResult"];
type SearchParams = operations["search"]["parameters"]["query"];
type SearchPathParams = operations["search"]["parameters"]["path"];

// Query Keys
const SEARCH_KEYS = {
	all: ["search"] as const,
	filterableAttributes: () =>
		[...SEARCH_KEYS.all, "filterable-attributes"] as const,
	results: (usercode: string, params: Partial<SearchParams>) =>
		[...SEARCH_KEYS.all, "results", usercode, params] as const,
	sortableAttributes: () =>
		[...SEARCH_KEYS.all, "sortable-attributes"] as const,
};

export type useSearchParams = Partial<SearchParams> & { query: string };
/**
 * Hook to search repository content with filtering and sorting
 */
export function useSearch(
	usercode: string,
	params: useSearchParams,
	enabled = true,
) {
	return useQuery({
		enabled: enabled && !!params.query?.trim() && !!usercode,
		queryFn: async () => {
			const searchParams = new URLSearchParams();

			// Add required query parameter
			searchParams.append("query", params.query);

			// Add optional filter parameters
			if (params.user) {
				searchParams.append("user", params.user);
			}
			if (params.week) {
				searchParams.append("week", params.week);
			}
			if (params.contribution_type) {
				searchParams.append("contribution_type", params.contribution_type);
			}
			if (params.repository) {
				searchParams.append("repository", params.repository);
			}
			if (params.author) {
				searchParams.append("author", params.author);
			}
			if (params.created_at_timestamp) {
				searchParams.append(
					"created_at_timestamp",
					params.created_at_timestamp,
				);
			}
			if (typeof params.is_selected === "boolean") {
				searchParams.append("is_selected", params.is_selected.toString());
			}
			if (params.sort) {
				searchParams.append("sort", params.sort);
			}
			if (params.limit) {
				searchParams.append("limit", params.limit.toString());
			}
			if (params.offset) {
				searchParams.append("offset", params.offset.toString());
			}

			const response = await apiClient.get<SearchResult>(
				`/search/${usercode}?${searchParams.toString()}`,
			);

			return response.data;
		},
		queryKey: SEARCH_KEYS.results(usercode, params),
		staleTime: 2 * 60 * 1000, // 2 minutes - search results can be more dynamic
	});
}

/**
 * Hook to get available sortable attributes
 */
export function useSortableAttributes() {
	return useQuery({
		queryFn: async () => {
			const response = await apiClient.get<unknown>(
				"/search/sortable-attributes",
			);
			return response.data;
		},
		queryKey: SEARCH_KEYS.sortableAttributes(),
		staleTime: 30 * 60 * 1000, // 30 minutes - metadata is relatively static
	});
}

/**
 * Hook to get available filterable attributes
 */
export function useFilterableAttributes() {
	return useQuery({
		queryFn: async () => {
			const response = await apiClient.get<unknown>(
				"/search/filterable-attributes",
			);
			return response.data;
		},
		queryKey: SEARCH_KEYS.filterableAttributes(),
		staleTime: 30 * 60 * 1000, // 30 minutes - metadata is relatively static
	});
}

// Export query keys and types for external use
export { SEARCH_KEYS };
export type { SearchResult, SearchParams, SearchPathParams };
