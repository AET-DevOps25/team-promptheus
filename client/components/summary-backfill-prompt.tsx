"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useContributions, useQueryClient } from "@/lib/api";
import { apiClient } from "@/lib/api/client";
import {
	type PageSummaryDto,
	useGenerateBackfillSummaries,
} from "@/lib/api/summary";

interface SummaryBackfillPromptProps {
	/**
	 * Optional custom message to display
	 */
	message?: string;
	/**
	 * Button variant
	 */
	variant?:
		| "default"
		| "outline"
		| "secondary"
		| "ghost"
		| "link"
		| "destructive";
	/**
	 * Button size
	 */
	size?: "default" | "sm" | "lg" | "icon";
	/**
	 * Custom class name for the button
	 */
	className?: string;
	/**
	 * Callback when backfill completes successfully
	 */
	onBackfillComplete?: () => void;
}

export function SummaryBackfillPrompt({
	message = "No summaries have been generated yet, but we found existing contributions.",
	variant = "default",
	size = "default",
	className = "gap-2",
	onBackfillComplete,
}: SummaryBackfillPromptProps) {
	const { toast } = useToast();
	const queryClient = useQueryClient();
	const [isPollingForSummaries, setIsPollingForSummaries] = useState(false);
	const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

	// Check for contributions
	const { data: contributionsPage } = useContributions(
		{ pageable: { page: 0, size: 1 } },
		true,
	);

	const hasContributions =
		contributionsPage?.content && contributionsPage.content.length > 0;

	// Backfill mutation
	const generateBackfillSummaries = useGenerateBackfillSummaries();

	// Polling effect for checking summaries after backfill
	useEffect(() => {
		if (isPollingForSummaries) {
			// Start polling every 3 seconds
			pollingIntervalRef.current = setInterval(async () => {
				// Refetch summaries to check for new data
				const summariesData = await queryClient.fetchQuery({
					queryKey: [
						"summaries",
						"list",
						{ size: 1, sort: ["createdAt,desc"] },
					],
					queryFn: async () => {
						const response = await apiClient.get<PageSummaryDto>(
							"/api/summaries?size=1&sort=createdAt,desc",
						);
						return response.data;
					},
				});

				// If summaries are found, stop polling
				if (summariesData?.content && summariesData.content.length > 0) {
					setIsPollingForSummaries(false);
					if (pollingIntervalRef.current) {
						clearInterval(pollingIntervalRef.current);
						pollingIntervalRef.current = null;
					}
					toast({
						title: "Summaries generated!",
						description:
							"Summary backfill completed successfully. The page has been updated.",
					});
					// Invalidate all summary queries to refresh the UI
					await queryClient.invalidateQueries({ queryKey: ["summaries"] });
					onBackfillComplete?.();
				}
			}, 3000);
		}

		return () => {
			if (pollingIntervalRef.current) {
				clearInterval(pollingIntervalRef.current);
				pollingIntervalRef.current = null;
			}
		};
	}, [isPollingForSummaries, toast, queryClient, onBackfillComplete]);

	// Cleanup polling on unmount
	useEffect(() => {
		return () => {
			if (pollingIntervalRef.current) {
				clearInterval(pollingIntervalRef.current);
			}
		};
	}, []);

	// Backfill handler
	const handleBackfill = async () => {
		try {
			await generateBackfillSummaries.mutateAsync();
			setIsPollingForSummaries(true);
			toast({
				title: "Backfill started",
				description:
					"Summary generation has been triggered. Waiting for summaries to be generated...",
			});
		} catch (_error) {
			toast({
				title: "Backfill failed",
				description:
					"There was an error starting the summary backfill process.",
				variant: "destructive",
			});
		}
	};

	// Don't render if no contributions exist
	if (!hasContributions) {
		return null;
	}

	return (
		<div className="text-center">
			<p className="text-gray-600 mb-4">{message}</p>
			<Button
				onClick={handleBackfill}
				disabled={generateBackfillSummaries.isPending || isPollingForSummaries}
				variant={variant}
				size={size}
				className={className}
			>
				{generateBackfillSummaries.isPending || isPollingForSummaries ? (
					<RefreshCw className="h-4 w-4 animate-spin" />
				) : (
					<RefreshCw className="h-4 w-4" />
				)}
				{generateBackfillSummaries.isPending
					? "Starting backfill..."
					: isPollingForSummaries
						? "Generating summaries..."
						: "Generate summaries from existing contributions"}
			</Button>
		</div>
	);
}
