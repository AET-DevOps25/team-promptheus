"use client";

import { format } from "date-fns";
import {
	Brain,
	CheckCircle,
	ChevronDown,
	ChevronRight,
	Clock,
	Lightbulb,
	Loader2,
	MessageCircleQuestion,
	Plus,
	Search,
	Send,
	TrendingUp,
} from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Markdown } from "@/components/ui/markdown";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import type { QuestionAnswerConstruct } from "@/lib/api";

interface QuestionAnswerProps {
	questionsAndAnswers: QuestionAnswerConstruct[];
	isLoading?: boolean;
	onSubmitQuestion?: (question: string) => void;
	isSubmitting?: boolean;
	username?: string;
	weekId?: string;
}

interface ParsedFullResponse {
	question_id?: string;
	user?: string;
	week?: string;
	question?: string;
	answer?: string;
	confidence?: number;
	evidence?: Array<{
		title?: string;
		contribution_id?: string;
		contribution_type?: string;
		excerpt?: string;
		relevance_score?: number;
		timestamp?: string;
	}>;
	reasoning_steps?: string[];
	suggested_actions?: string[];
	asked_at?: string;
	response_time_ms?: number;
	conversation_id?: string;
}

export function QuestionAnswerSection({
	questionsAndAnswers,
	isLoading,
	onSubmitQuestion,
	isSubmitting = false,
	username,
	weekId,
}: QuestionAnswerProps) {
	const [question, setQuestion] = useState("");

	const handleSubmitQuestion = () => {
		if (!question.trim() || !onSubmitQuestion) return;
		onSubmitQuestion(question.trim());
		setQuestion("");
	};

	return (
		<div className="space-y-6">
			{/* Ask Question Section */}
			{onSubmitQuestion && (
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<Plus className="h-5 w-5" />
							Ask a Question
						</CardTitle>
						<CardDescription>
							Ask anything about {username ? `${username}'s` : "this"}{" "}
							contributions for week {weekId}
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="space-y-4">
							<Textarea
								className="resize-none"
								onChange={(e) => setQuestion(e.target.value)}
								placeholder="e.g., What were the main accomplishments this week? Any blockers encountered? What should be prioritized next?"
								rows={4}
								value={question}
							/>
							<div className="flex justify-between items-center">
								<p className="text-xs text-muted-foreground">
									AI will analyze the contributions to provide contextual
									answers
								</p>
								<Button
									disabled={isSubmitting || !question.trim()}
									onClick={handleSubmitQuestion}
								>
									{isSubmitting ? (
										<>
											<Loader2 className="h-4 w-4 animate-spin mr-2" />
											Analyzing...
										</>
									) : (
										<>
											<Send className="h-4 w-4 mr-2" />
											Ask Question
										</>
									)}
								</Button>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Q&A List */}
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<div className="p-2 bg-purple-100 rounded-full">
							<MessageCircleQuestion className="h-4 w-4 text-purple-600" />
						</div>
						Questions & Answers{" "}
						{questionsAndAnswers.length > 0 &&
							`(${questionsAndAnswers.length})`}
					</CardTitle>
				</CardHeader>
				<CardContent>
					{isLoading ? (
						<QuestionAnswerLoading />
					) : questionsAndAnswers.length === 0 ? (
						<div className="text-center py-8 text-muted-foreground">
							<MessageCircleQuestion className="h-8 w-8 mx-auto mb-2 opacity-50" />
							<p className="text-sm">No questions asked yet for this week</p>
							<p className="text-xs">
								Ask the first question to get AI-powered insights!
							</p>
						</div>
					) : (
						<div className="space-y-4">
							{questionsAndAnswers.map((qa, index) => (
								<QuestionAnswerItem key={qa.genaiQuestionId || index} qa={qa} />
							))}
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);
}

interface QuestionAnswerItemProps {
	qa: QuestionAnswerConstruct;
}

function QuestionAnswerItem({ qa }: QuestionAnswerItemProps) {
	const [isExpanded, setIsExpanded] = useState(false);
	const [showEvidence, setShowEvidence] = useState(false);
	const [showReasoning, setShowReasoning] = useState(false);

	const formatDate = (dateString?: string) => {
		if (!dateString) return "Unknown time";
		try {
			return format(new Date(dateString), "MMM d, yyyy 'at' h:mm a");
		} catch {
			return "Invalid date";
		}
	};

	const getConfidenceColor = (confidence?: number) => {
		if (!confidence) return "bg-gray-100 text-gray-600";
		if (confidence >= 0.8) return "bg-green-100 text-green-700";
		if (confidence >= 0.6) return "bg-yellow-100 text-yellow-700";
		return "bg-red-100 text-red-700";
	};

	const getConfidenceText = (confidence?: number) => {
		if (!confidence) return "Unknown";
		return `${Math.round(confidence * 100)}%`;
	};

	// Parse the fullResponse JSON
	const parsedResponse: ParsedFullResponse | null = (() => {
		if (!qa.fullResponse) return null;
		try {
			return JSON.parse(qa.fullResponse);
		} catch {
			return null;
		}
	})();

	const evidence = parsedResponse?.evidence || [];
	const reasoningSteps = parsedResponse?.reasoning_steps || [];
	const suggestedActions = parsedResponse?.suggested_actions || [];

	return (
		<div className="border rounded-lg overflow-hidden">
			{/* Main Q&A Content */}
			<div className="p-4 space-y-3">
				{/* Question */}
				{qa.questionText && (
					<div className="space-y-2">
						<div className="flex items-start gap-2">
							<MessageCircleQuestion className="h-4 w-4 text-purple-600 mt-1 flex-shrink-0" />
							<div className="flex-1">
								<p className="font-medium text-gray-900">{qa.questionText}</p>
							</div>
						</div>
					</div>
				)}

				{/* Answer */}
				<div className="space-y-2">
					<div className="flex items-start gap-2">
						<Brain className="h-4 w-4 text-blue-600 mt-1 flex-shrink-0" />
						<div className="flex-1">
							<Markdown variant="default">{qa.answer}</Markdown>
						</div>
					</div>
				</div>

				{/* Metadata */}
				<div className="flex flex-wrap items-center gap-2 pt-2 border-t text-sm text-gray-500">
					{qa.confidence && (
						<Badge
							className={getConfidenceColor(qa.confidence)}
							variant="outline"
						>
							<TrendingUp className="h-3 w-3 mr-1" />
							Confidence: {getConfidenceText(qa.confidence)}
						</Badge>
					)}

					{qa.askedAt && (
						<Badge className="bg-blue-50 text-blue-700" variant="outline">
							<Clock className="h-3 w-3 mr-1" />
							{formatDate(qa.askedAt)}
						</Badge>
					)}

					{qa.responseTimeMs && (
						<Badge className="bg-gray-50 text-gray-600" variant="outline">
							⚡ {qa.responseTimeMs}ms
						</Badge>
					)}

					{evidence.length > 0 && (
						<Badge className="bg-purple-50 text-purple-700" variant="outline">
							<Search className="h-3 w-3 mr-1" />
							{evidence.length} evidence
						</Badge>
					)}

					{/* Expand/Collapse Button */}
					{(evidence.length > 0 ||
						reasoningSteps.length > 0 ||
						suggestedActions.length > 0) && (
						<Button
							className="ml-auto"
							onClick={() => setIsExpanded(!isExpanded)}
							size="sm"
							variant="ghost"
						>
							{isExpanded ? (
								<>
									<ChevronDown className="h-4 w-4 mr-1" />
									Show Less
								</>
							) : (
								<>
									<ChevronRight className="h-4 w-4 mr-1" />
									Show Details
								</>
							)}
						</Button>
					)}
				</div>
			</div>

			{/* Expanded Details */}
			{isExpanded && (
				<div className="border-t bg-gray-50">
					<div className="p-4 space-y-4">
						{/* Evidence Section */}
						{evidence.length > 0 && (
							<Collapsible onOpenChange={setShowEvidence} open={showEvidence}>
								<CollapsibleTrigger asChild>
									<Button
										className="w-full justify-start p-0 h-auto"
										variant="ghost"
									>
										<div className="flex items-center gap-2">
											{showEvidence ? (
												<ChevronDown className="h-4 w-4" />
											) : (
												<ChevronRight className="h-4 w-4" />
											)}
											<Search className="h-4 w-4 text-purple-600" />
											<span className="font-medium">
												Evidence ({evidence.length})
											</span>
										</div>
									</Button>
								</CollapsibleTrigger>
								<CollapsibleContent className="mt-2">
									<div className="space-y-2">
										{evidence.slice(0, 5).map((item) => (
											<div
												className="bg-white p-3 rounded border text-sm"
												key={`evidence-${(item.title || "untitled").slice(0, 30).replace(/\s+/g, "-")}-${item.relevance_score || 0}`}
											>
												<div className="flex items-start justify-between gap-2 mb-1">
													<p className="font-medium text-gray-900">
														{item.title || "Untitled"}
													</p>
													{item.relevance_score && (
														<Badge className="text-xs" variant="outline">
															{Math.round(item.relevance_score * 100)}% match
														</Badge>
													)}
												</div>
												{item.excerpt && (
													<p className="text-gray-600 text-xs leading-relaxed">
														{item.excerpt}
													</p>
												)}
												<div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
													{item.contribution_type && (
														<Badge className="text-xs" variant="secondary">
															{item.contribution_type}
														</Badge>
													)}
													{item.timestamp && (
														<span>{formatDate(item.timestamp)}</span>
													)}
												</div>
											</div>
										))}
										{evidence.length > 5 && (
											<p className="text-xs text-gray-500 text-center py-2">
												... and {evidence.length - 5} more evidence items
											</p>
										)}
									</div>
								</CollapsibleContent>
							</Collapsible>
						)}

						{/* Reasoning Steps */}
						{reasoningSteps.length > 0 && (
							<Collapsible onOpenChange={setShowReasoning} open={showReasoning}>
								<CollapsibleTrigger asChild>
									<Button
										className="w-full justify-start p-0 h-auto"
										variant="ghost"
									>
										<div className="flex items-center gap-2">
											{showReasoning ? (
												<ChevronDown className="h-4 w-4" />
											) : (
												<ChevronRight className="h-4 w-4" />
											)}
											<Brain className="h-4 w-4 text-blue-600" />
											<span className="font-medium">
												AI Reasoning ({reasoningSteps.length} steps)
											</span>
										</div>
									</Button>
								</CollapsibleTrigger>
								<CollapsibleContent className="mt-2">
									<div className="space-y-2">
										{reasoningSteps.map((step, index) => (
											<div
												className="bg-white p-3 rounded border flex items-start gap-2"
												key={`reasoning-step-${step.slice(0, 40).replace(/\s+/g, "-")}`}
											>
												<div className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
													{index + 1}
												</div>
												<p className="text-sm text-gray-700 leading-relaxed">
													{step}
												</p>
											</div>
										))}
									</div>
								</CollapsibleContent>
							</Collapsible>
						)}

						{/* Suggested Actions */}
						{suggestedActions.length > 0 && (
							<div>
								<div className="flex items-center gap-2 mb-2">
									<Lightbulb className="h-4 w-4 text-amber-600" />
									<span className="font-medium">Suggested Actions</span>
								</div>
								<div className="space-y-2">
									{suggestedActions.map((action) => (
										<div
											className="bg-amber-50 border border-amber-200 p-3 rounded flex items-start gap-2"
											key={action}
										>
											<CheckCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
											<p className="text-sm text-amber-800 leading-relaxed">
												{action}
											</p>
										</div>
									))}
								</div>
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
}

function QuestionAnswerLoading() {
	return (
		<div className="space-y-4">
			{Array.from({ length: 2 }).map((_, i) => (
				// biome-ignore lint/suspicious/noArrayIndexKey: We just need something, this is a static array
				<div className="border rounded-lg p-4 space-y-3" key={i}>
					<div className="flex items-start gap-2">
						<Skeleton className="h-4 w-4 mt-1" />
						<Skeleton className="h-4 flex-1" />
					</div>
					<div className="flex items-start gap-2">
						<Skeleton className="h-4 w-4 mt-1" />
						<div className="flex-1 space-y-2">
							<Skeleton className="h-4 w-full" />
							<Skeleton className="h-4 w-3/4" />
						</div>
					</div>
					<div className="flex gap-2 pt-2">
						<Skeleton className="h-6 w-20" />
						<Skeleton className="h-6 w-24" />
						<Skeleton className="h-6 w-16" />
					</div>
				</div>
			))}
		</div>
	);
}
