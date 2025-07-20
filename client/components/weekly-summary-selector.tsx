// @ts-nocheck
"use client";

import { Calendar, Send } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { useGenerateSummary } from "@/lib/api/summary";

interface WeeklySummarySelectorProps {
	userId: string;
}

export function WeeklySummarySelector({ userId }: WeeklySummarySelectorProps) {
	const [isGenerating, setIsGenerating] = useState(false);
	const generateSummary = useGenerateSummary();

	const handleGenerateDemo = async () => {
		setIsGenerating(true);
		try {
			// Demo values for testing
			await generateSummary.mutateAsync({
				owner: "AET-DevOps25",
				repo: "team-promptheus",
				username: "WoH",
				week: "2025-W30",
			});

			alert("Summary generation started! Check the dashboard for results.");
		} catch (error) {
			console.error("Failed to generate summary:", error);
			alert("Failed to generate summary. Check console for details.");
		} finally {
			setIsGenerating(false);
		}
	};

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<Calendar className="h-5 w-5" />
					Generate Weekly Summary
				</CardTitle>
				<CardDescription>
					Simple form to test weekly summary generation functionality
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-6">
				<div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
					<h4 className="font-medium text-blue-900 mb-2">Demo Configuration</h4>
					<div className="space-y-1 text-sm text-blue-800">
						<p>
							<strong>Repository:</strong> AET-DevOps25/team-promptheus
						</p>
						<p>
							<strong>User:</strong> WoH
						</p>
						<p>
							<strong>Week:</strong> 2025-W30
						</p>
						<p>
							<strong>User ID:</strong> {userId}
						</p>
					</div>
				</div>

				<Button
					onClick={handleGenerateDemo}
					disabled={isGenerating}
					className="w-full"
					size="lg"
				>
					{isGenerating ? (
						<>
							<span className="animate-spin mr-2">⏳</span>
							Generating Summary...
						</>
					) : (
						<>
							<Send className="mr-2 h-4 w-4" />
							Generate Demo Weekly Summary
						</>
					)}
				</Button>

				{isGenerating && (
					<div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
						<p className="text-green-800 font-medium">
							✨ Generating your weekly summary...
						</p>
						<p className="text-sm text-green-700 mt-1">
							This will take a moment. Check the dashboard for results!
						</p>
					</div>
				)}
			</CardContent>
		</Card>
	);
}
