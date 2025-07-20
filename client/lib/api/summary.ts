/**
 * Summary API service with TanStack Query hooks
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { components, operations } from "./types/summary";

// Extract types from OpenAPI schema
export type SummaryDto = components["schemas"]["SummaryDto"];
export type PageSummaryDto = components["schemas"]["PageSummaryDto"];
export type Pageable = components["schemas"]["Pageable"];

type GenerateSummaryParams =
	operations["generateSummary"]["parameters"]["path"];

// Enhanced interface for summary filters with pagination
export interface SummaryFilters {
	week?: string;
	username?: string;
	repository?: string;
	page?: number;
	size?: number;
	sort?: string[];
}

// Query Keys
const SUMMARY_KEYS = {
	all: ["summaries"] as const,
	detail: (id: number) => [...SUMMARY_KEYS.all, "detail", id] as const,
	list: (params?: SummaryFilters) =>
		[...SUMMARY_KEYS.all, "list", params] as const,
	lists: () => [...SUMMARY_KEYS.all, "list"] as const,
};

/**
 * Hook to fetch summaries with filtering and pagination
 */
export function useSummaries(filters?: SummaryFilters, enabled = true) {
	return useQuery({
		enabled,
		queryFn: async () => {
			const searchParams = new URLSearchParams();

			// Add filtering parameters
			if (filters?.week) {
				searchParams.append("week", filters.week);
			}
			if (filters?.username) {
				searchParams.append("username", filters.username);
			}
			if (filters?.repository) {
				searchParams.append("repository", filters.repository);
			}

			// Add pagination parameters
			if (filters?.page !== undefined) {
				searchParams.append("page", filters.page.toString());
			}
			if (filters?.size !== undefined) {
				searchParams.append("size", filters.size.toString());
			}
			if (filters?.sort?.length) {
				filters.sort.forEach((sortParam) => {
					searchParams.append("sort", sortParam);
				});
			}

			const queryString = searchParams.toString();
			const url = queryString
				? `/api/summaries?${queryString}`
				: "/api/summaries";

			const response = await apiClient.get<PageSummaryDto>(url);
			return response.data;
		},
		queryKey: SUMMARY_KEYS.list(filters),
		staleTime: 5 * 60 * 1000, // 5 minutes - summaries don't change very frequently
	});
}

/**
 * Hook to generate a new summary
 */
export function useGenerateSummary() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (params: GenerateSummaryParams) => {
			const { owner, repo, username, week } = params;
			const response = await apiClient.post<void>(
				`/api/summaries/${owner}/${repo}/${username}/${week}`,
			);
			return response.data;
		},
		onSuccess: () => {
			// Invalidate and refetch summary queries
			queryClient.invalidateQueries({ queryKey: SUMMARY_KEYS.all });
		},
	});
}

/**
 * Hook to generate backfill summaries for all repositories and users
 */
export function useGenerateBackfillSummaries() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async () => {
			const response = await apiClient.post<void>("/api/summaries/backfill");
			return response.data;
		},
		onSuccess: () => {
			// Invalidate and refetch summary queries
			queryClient.invalidateQueries({ queryKey: SUMMARY_KEYS.all });
		},
	});
}
