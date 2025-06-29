/**
 * Search API service with TanStack Query hooks
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";

import type { components, operations } from "./types/search";

export type SearchResult = components["schemas"]["SearchResult"];
export type SearchParams = operations["search"]["parameters"]["query"];
export type SearchPathParams = operations["search"]["parameters"]["path"];

// Query Keys
export const SEARCH_KEYS = {
  all: ["search"] as const,
  results: (usercode: string, params: useSearchParams) =>
    [...SEARCH_KEYS.all, "results", usercode, params] as const,
};

export type useSearchParams = Partial<SearchParams> & { query: string };
/**
 * Hook to search repository content with filtering and sorting
 */
export function useSearch(usercode: string, params: useSearchParams, enabled = true) {
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
        searchParams.append("created_at_timestamp", params.created_at_timestamp);
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
