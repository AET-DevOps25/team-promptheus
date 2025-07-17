/**
 * Server API service with TanStack Query hooks
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { components } from "./types/server";

// Types
export type GitRepoInformation =
	components["schemas"]["GitRepoInformationConstruct"];

// Extend QuestionSubmission with username and optional gitRepositoryId fields that the server expects
export type QuestionSubmission = components["schemas"]["QuestionSubmission"] & {
	username: string;
	gitRepositoryId?: number;
};

// Extend QuestionAnswerConstruct with rich fields from V9 migration
export type QuestionAnswerConstruct =
	components["schemas"]["QuestionAnswerConstruct"] & {
		confidence?: number;
		genaiQuestionId?: string;
		userName?: string;
		weekId?: string;
		questionText?: string;
		fullResponse?: string;
		askedAt?: string;
		responseTimeMs?: number;
		conversationId?: string;
	};

export type PATConstruct = components["schemas"]["PATConstruct"];
export type LinkConstruct = components["schemas"]["LinkConstruct"];

// Query Keys
export const SERVER_KEYS = {
	all: ["server"] as const,
	qa: (username: string, weekId: string) =>
		[...SERVER_KEYS.all, "qa", username, weekId] as const,
	repo: (usercode: string) => [...SERVER_KEYS.all, "repo", usercode] as const,
};

// Get repository info
export function useGitRepoInformation(usercode: string, enabled = true) {
	return useQuery({
		enabled: enabled && !!usercode,
		queryFn: async () => {
			const response = await apiClient.get<GitRepoInformation>(
				`/api/repositories/${usercode}`,
			);
			return response.data;
		},
		queryKey: SERVER_KEYS.repo(usercode),
		staleTime: 5 * 60 * 1000, // 5 minutes
	});
}

// Create a question for the repo
export function useCreateQuestion(usercode: string) {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: async (question: QuestionSubmission) => {
			const response = await apiClient.post<QuestionAnswerConstruct>(
				`/api/repositories/${usercode}/question`,
				question,
			);
			return response.data;
		},
		onSuccess: () => {
			// Invalidate repo info to refresh questions
			queryClient.invalidateQueries({ queryKey: SERVER_KEYS.repo(usercode) });

			// Invalidate all Q&A queries to ensure fresh data
			queryClient.invalidateQueries({ queryKey: SERVER_KEYS.all });
		},
	});
}

// Get Q&A for specific user and week
export function useQuestionsAndAnswers(
	username: string,
	weekId: string,
	enabled = true,
) {
	return useQuery({
		enabled: enabled && !!username && !!weekId,
		queryFn: async () => {
			const response = await apiClient.get<QuestionAnswerConstruct[]>(
				`/api/repositories/questions/${username}/${weekId}`,
			);
			return response.data;
		},
		queryKey: SERVER_KEYS.qa(username, weekId),
		staleTime: 5 * 60 * 1000, // 5 minutes
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
