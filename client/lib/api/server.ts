/**
 * Server API service with TanStack Query hooks
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { components } from "./types/server";

// Types
export type GitRepoInformation =
	components["schemas"]["GitRepoInformationConstruct"];
export type QuestionSubmission = components["schemas"]["QuestionSubmission"];
export type PATConstruct = components["schemas"]["PATConstruct"];
export type LinkConstruct = components["schemas"]["LinkConstruct"];

// Query Keys
export const SERVER_KEYS = {
	all: ["server"] as const,
	repo: (usercode: string) => [...SERVER_KEYS.all, "repo", usercode] as const,
};

// Get repository info
export function useGitRepoInformation(usercode: string, enabled = true) {
	return useQuery({
		enabled: enabled && !!usercode,
		queryKey: SERVER_KEYS.repo(usercode),
		queryFn: async () => {
			const response = await apiClient.get<GitRepoInformation>(
				`/api/repositories/${usercode}`,
			);
			return response.data;
		},
		staleTime: 5 * 60 * 1000, // 5 minutes
	});
}

// Create a question for the repo
export function useCreateQuestion(usercode: string) {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: async (question: QuestionSubmission) => {
			const response = await apiClient.post<string>(
				`/api/repositories/${usercode}/question`,
				question,
			);
			return response.data;
		},
		onSuccess: () => {
			// Invalidate repo info to refresh questions
			queryClient.invalidateQueries({ queryKey: SERVER_KEYS.repo(usercode) });
		},
	});
}

// Create from PAT (Personal Access Token)
export function useCreateFromPAT() {
	return useMutation({
		mutationFn: async (patData: PATConstruct) => {
			const response = await apiClient.post<LinkConstruct>(
				"/api/repositories/PAT",
				patData,
			);
			return response.data;
		},
	});
}
