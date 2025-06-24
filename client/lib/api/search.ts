/**
 * Search API service with TanStack Query hooks
 */

import { useQuery } from "@tanstack/react-query";
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

// Export query keys for external use
export { SEARCH_KEYS };
