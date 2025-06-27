/**
 * QA API service with TanStack Query hooks
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
	CreateQARequest,
	CreateQAResponse,
	QAItem,
	QAResponse,
	QueryKeys,
	StatusUpdateRequest,
	VoteRequest,
	VoteResponse,
} from "./types";

// Query Keys
const QA_KEYS = {
	all: ["qa"] as const,
	item: (id: string) => [...QA_KEYS.all, "item", id] as const,
	items: () => [...QA_KEYS.all, "items"] as const,
};

/**
 * Hook to fetch all QA items
 */
export function useQAItems() {
	return useQuery({
		queryFn: async () => {
			const response = await apiClient.get<QAResponse>("/qa");
			return response.data;
		},
		queryKey: QA_KEYS.items(),
		staleTime: 5 * 60 * 1000, // 5 minutes
	});
}

/**
 * Hook to create a new QA item
 */
export function useCreateQA() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (request: CreateQARequest) => {
			const response = await apiClient.post<CreateQAResponse>("/qa", request);
			return response.data;
		},
		onSuccess: (data) => {
			// Update the QA items cache with the new item
			queryClient.setQueryData<QAResponse>(QA_KEYS.items(), (old) => {
				if (!old) return { items: [data.item], total: 1 };
				return {
					items: [data.item, ...old.items],
					total: old.total + 1,
				};
			});
			// Invalidate to refetch from server
			queryClient.invalidateQueries({ queryKey: QA_KEYS.all });
		},
	});
}

/**
 * Hook to update QA item status
 */
export function useUpdateQAStatus() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async ({
			id,
			status,
		}: {
			id: string;
			status: "approved" | "rejected";
		}) => {
			const response = await apiClient.patch<QAItem>(`/qa/${id}`, { status });
			return { id, item: response.data };
		},
		onSuccess: ({ id, item }) => {
			// Update the specific item in the cache
			queryClient.setQueryData<QAResponse>(QA_KEYS.items(), (old) => {
				if (!old) return old;
				return {
					...old,
					items: old.items.map((qaItem) =>
						qaItem.id === id ? { ...qaItem, status: item.status } : qaItem,
					),
				};
			});
		},
	});
}

/**
 * Hook to vote on a QA item
 */
export function useVoteQA() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async ({ id, type }: { id: string; type: "up" | "down" }) => {
			const response = await apiClient.post<VoteResponse>(`/qa/${id}/vote`, {
				type,
			});
			return { id, votes: response.data };
		},
		onSuccess: ({ id, votes }) => {
			// Update the specific item's votes in the cache
			queryClient.setQueryData<QAResponse>(QA_KEYS.items(), (old) => {
				if (!old) return old;
				return {
					...old,
					items: old.items.map((item) =>
						item.id === id
							? {
									...item,
									downvotes: votes.downvotes,
									upvotes: votes.upvotes,
								}
							: item,
					),
				};
			});
		},
	});
}

/**
 * Hook to get a single QA item by ID
 */
export function useQAItem(id: string) {
	return useQuery({
		enabled: !!id,
		queryFn: async () => {
			const response = await apiClient.get<QAItem>(`/qa/${id}`);
			return response.data;
		},
		queryKey: QA_KEYS.item(id),
		staleTime: 5 * 60 * 1000, // 5 minutes
	});
}

// Export query keys for external use
export { QA_KEYS };
