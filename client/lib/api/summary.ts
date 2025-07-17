/**
 * Summary API service with TanStack Query hooks
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { components, operations } from "./types/summary";

// Extract types from OpenAPI schema
export type Summary = components["schemas"]["Summary"];
type GetSummariesParams = operations["getSummaries"]["parameters"]["query"];
type GenerateSummaryParams =
	operations["generateSummary"]["parameters"]["path"];

// Query Keys
const SUMMARY_KEYS = {
	all: ["summaries"] as const,
	detail: (id: number) => [...SUMMARY_KEYS.all, "detail", id] as const,
	list: (params?: GetSummariesParams) =>
		[...SUMMARY_KEYS.all, "list", params] as const,
	lists: () => [...SUMMARY_KEYS.all, "list"] as const,
};

/**
 * Hook to fetch summaries with optional week filtering
 */
export function useSummaries(params?: GetSummariesParams, enabled = true) {
	return useQuery({
		enabled,
		queryFn: async () => {
			const searchParams = new URLSearchParams();

			// Add optional week filter
			if (params?.week) {
				searchParams.append("week", params.week);
			}

			const queryString = searchParams.toString();
			const url = queryString
				? `/api/summaries?${queryString}`
				: "/api/summaries";

			const response = await apiClient.get<Summary[]>(url);
			return response.data;
		},
		queryKey: SUMMARY_KEYS.list(params),
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
