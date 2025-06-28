/**
 * Contributions API service with TanStack Query hooks
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { components, operations } from "./types/contribution";

// Extract types from OpenAPI schema
type ContributionDto = components["schemas"]["ContributionDto"];
type Page = components["schemas"]["Page"];
type PageContributionDto = components["schemas"]["PageContributionDto"];
type TriggerResponse = components["schemas"]["TriggerResponse"];
type TriggerRequest = components["schemas"]["TriggerRequest"];
type Pageable = components["schemas"]["Pageable"];
type GetContributionsParams =
	operations["getContributions"]["parameters"]["query"];

// Query Keys
const CONTRIBUTION_KEYS = {
	all: ["contributions"] as const,
	list: (params: Partial<GetContributionsParams>) =>
		[...CONTRIBUTION_KEYS.all, "list", params] as const,
	lists: () => [...CONTRIBUTION_KEYS.all, "list"] as const,
};

/**
 * Hook to fetch contributions with filtering and pagination
 */
export function useContributions(
	params: Partial<GetContributionsParams> & { pageable: Pageable },
	enabled = true,
) {
	return useQuery({
		enabled,
		queryFn: async () => {
			const searchParams = new URLSearchParams();

			// Add optional filter parameters
			if (params.contributor) {
				searchParams.append("contributor", params.contributor);
			}
			if (params.startDate) {
				searchParams.append("startDate", params.startDate);
			}
			if (params.endDate) {
				searchParams.append("endDate", params.endDate);
			}

			// Add pagination parameters
			if (params.pageable.page !== undefined) {
				searchParams.append("page", params.pageable.page.toString());
			}
			if (params.pageable.size !== undefined) {
				searchParams.append("size", params.pageable.size.toString());
			}
			if (params.pageable.sort) {
				params.pageable.sort.forEach((sortParam) => {
					searchParams.append("sort", sortParam);
				});
			}

			const response = await apiClient.get<Page>(
				`/contributions?${searchParams.toString()}`,
			);

			return response.data;
		},
		queryKey: CONTRIBUTION_KEYS.list(params),
		staleTime: 5 * 60 * 1000, // 5 minutes - contributions don't change very frequently
	});
}

/**
 * Hook to update contribution selection status
 */
export function useUpdateContributions() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (contributions: ContributionDto[]) => {
			const response = await apiClient.put<string>(
				"/contributions",
				contributions,
			);
			return response.data;
		},
		onSuccess: () => {
			// Invalidate all contribution queries to refetch updated data
			queryClient.invalidateQueries({ queryKey: CONTRIBUTION_KEYS.all });
		},
	});
}

/**
 * Hook to trigger contribution fetch for all repositories
 */
export function useTriggerContributionFetch() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async () => {
			const response = await apiClient.post<TriggerResponse>(
				"/contributions/trigger",
			);
			return response.data;
		},
		onSuccess: () => {
			// Invalidate all contribution queries since new contributions may have been fetched
			queryClient.invalidateQueries({ queryKey: CONTRIBUTION_KEYS.all });
		},
	});
}

/**
 * Hook to trigger contribution fetch for a specific repository
 */
export function useTriggerContributionFetchForRepository() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (request: TriggerRequest) => {
			const response = await apiClient.post<TriggerResponse>(
				"/contributions/trigger/repository",
				request,
			);
			return response.data;
		},
		onSuccess: () => {
			// Invalidate all contribution queries since new contributions may have been fetched
			queryClient.invalidateQueries({ queryKey: CONTRIBUTION_KEYS.all });
		},
	});
}

// Export query keys and types for external use
export { CONTRIBUTION_KEYS };
export type {
	ContributionDto,
	Page,
	PageContributionDto,
	TriggerResponse,
	TriggerRequest,
	Pageable,
	GetContributionsParams,
};
