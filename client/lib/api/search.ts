/**
 * Search API service with TanStack Query hooks
 */

import { useQuery } from "@tanstack/react-query";
import React from "react";
import { apiClient } from "./client";
import type { SearchParams, SearchResponse, SearchResult } from "./types";

// Query Keys
const SEARCH_KEYS = {
	all: ["search"] as const,
	results: (params: SearchParams) =>
		[...SEARCH_KEYS.all, "results", params] as const,
};

/**
 * Hook to search for content across repositories
 */
export function useSearch(params: SearchParams, enabled = true) {
	return useQuery({
		enabled: enabled && !!params.query?.trim(),
		queryFn: async () => {
			const searchParams = new URLSearchParams();

			// Add query parameter
			if (params.query) {
				searchParams.append("query", params.query);
			}

			// Add filter parameters
			if (params.filterContributionType?.length) {
				searchParams.append(
					"filterContributionType",
					params.filterContributionType.join(","),
				);
			}

			if (params.repositories?.length) {
				searchParams.append("repositories", params.repositories.join(","));
			}

			if (params.authors?.length) {
				searchParams.append("authors", params.authors.join(","));
			}

			if (params.dateFrom) {
				searchParams.append("dateFrom", params.dateFrom);
			}

			if (params.dateTo) {
				searchParams.append("dateTo", params.dateTo);
			}

			const response = await apiClient.get<SearchResult[]>(
				`/search?${searchParams.toString()}`,
			);

			// Transform the response to match expected format
			return {
				filters: {
					authors: params.authors || [],
					contributionTypes: params.filterContributionType || [],
					dateFrom: params.dateFrom,
					dateTo: params.dateTo,
					repositories: params.repositories || [],
				},
				query: params.query,
				results: response.data,
				total: response.data.length,
			} as SearchResponse;
		},
		queryKey: SEARCH_KEYS.results(params),
		staleTime: 2 * 60 * 1000, // 2 minutes - search results can be more dynamic
	});
}

/**
 * Hook for debounced search - useful for search-as-you-type functionality
 */
export function useDebouncedSearch(
	params: SearchParams,
	debounceMs = 500,
	enabled = true,
) {
	const [debouncedParams, setDebouncedParams] = React.useState(params);

	React.useEffect(() => {
		const timer = setTimeout(() => {
			setDebouncedParams(params);
		}, debounceMs);

		return () => clearTimeout(timer);
	}, [params, debounceMs]);

	return useSearch(debouncedParams, enabled);
}

/**
 * Hook to get search suggestions based on query
 */
export function useSearchSuggestions(query: string, enabled = true) {
	return useQuery({
		enabled: enabled && query.length >= 2,
		queryFn: async () => {
			// This would typically call a suggestions endpoint
			// For now, we'll return some mock suggestions based on the query
			const suggestions = [
				`${query} performance`,
				`${query} bug`,
				`${query} feature`,
				`${query} optimization`,
				`${query} refactor`,
			].filter((suggestion) => suggestion !== query);

			return suggestions.slice(0, 5);
		},
		queryKey: [...SEARCH_KEYS.all, "suggestions", query],
		staleTime: 5 * 60 * 1000, // 5 minutes
	});
}

// Export query keys for external use
export { SEARCH_KEYS };
