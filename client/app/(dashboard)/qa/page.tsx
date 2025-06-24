"use client";

import {
	Bot,
	CheckCircle,
	Clock,
	Loader2,
	MessageSquare,
	Plus,
	Send,
	ThumbsDown,
	ThumbsUp,
	User,
	XCircle,
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
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
	useCreateQA,
	useQAItems,
	useUpdateQAStatus,
	useVoteQA,
} from "@/lib/api";
import type { QAItem } from "@/lib/api/types";

export default function QAPage() {
	const [question, setQuestion] = useState("");
	const [selectedForReport, setSelectedForReport] = useState<string[]>([]);
	const [filter, setFilter] = useState<
		"all" | "pending" | "approved" | "rejected"
	>("all");

	// TanStack Query hooks
	const { data: qaResponse, isLoading: isLoadingItems, error } = useQAItems();
	const createQAMutation = useCreateQA();
	const updateStatusMutation = useUpdateQAStatus();
	const voteMutation = useVoteQA();

	const qaItems = qaResponse?.items || [];

	const handleSubmitQuestion = async () => {
		if (!question.trim()) return;

		try {
			await createQAMutation.mutateAsync({
				question: question.trim(),
			});
			setQuestion("");
		} catch (error) {
			console.error("Failed to submit question:", error);
		}
	};

	const handleStatusUpdate = async (
		id: string,
		status: "approved" | "rejected",
	) => {
		try {
			await updateStatusMutation.mutateAsync({ id, status });
		} catch (error) {
			console.error("Failed to update status:", error);
		}
	};

	const handleVote = async (id: string, type: "up" | "down") => {
		try {
			await voteMutation.mutateAsync({ id, type });
		} catch (error) {
			console.error("Failed to vote:", error);
		}
	};

	const toggleReportSelection = (id: string) => {
		setSelectedForReport((prev) =>
			prev.includes(id)
				? prev.filter((itemId) => itemId !== id)
				: [...prev, id],
		);
	};

	const filteredItems = qaItems.filter((item: QAItem) => {
		if (filter === "all") return true;
		return item.status === filter;
	});

	const getStatusIcon = (status: QAItem["status"]) => {
		switch (status) {
			case "approved":
				return <CheckCircle className="h-4 w-4 text-green-600" />;
			case "rejected":
				return <XCircle className="h-4 w-4 text-red-600" />;
			default:
				return <Clock className="h-4 w-4 text-yellow-600" />;
		}
	};

	const getStatusColor = (status: QAItem["status"]) => {
		switch (status) {
			case "approved":
				return "bg-green-100 text-green-800";
			case "rejected":
				return "bg-red-100 text-red-800";
			default:
				return "bg-yellow-100 text-yellow-800";
		}
	};

	return (
		<>
			<header className="border-b bg-white">
				<div className="container mx-auto px-4 py-4">
					<div className="flex items-center gap-2">
						<MessageSquare className="h-6 w-6" />
						<h1 className="text-2xl font-bold">Questions & Answers</h1>
					</div>
					<p className="text-slate-600">
						Ask questions about your repositories and get AI-powered answers
					</p>
				</div>
			</header>

			<main className="container mx-auto px-4 py-8 max-w-6xl">
				<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
					{/* Ask Question Section */}
					<div className="lg:col-span-2">
						<Card className="mb-8">
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Plus className="h-5 w-5" />
									Ask a Question
								</CardTitle>
								<CardDescription>
									Ask anything about your repositories - code patterns, recent
									changes, team activity, or technical decisions
								</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									<Textarea
										className="resize-none"
										onChange={(e) => setQuestion(e.target.value)}
										placeholder="e.g., What are the main performance bottlenecks in our API? What security improvements were made last month? Which components need refactoring?"
										rows={4}
										value={question}
									/>
									<div className="flex justify-between items-center">
										<p className="text-xs text-muted-foreground">
											AI will analyze your repositories to provide contextual
											answers
										</p>
										<Button
											disabled={createQAMutation.isPending || !question.trim()}
											onClick={handleSubmitQuestion}
										>
											{createQAMutation.isPending ? (
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

						{/* Filter Tabs */}
						<div className="flex gap-2 mb-6">
							{[
								{ key: "all", label: "All Questions" },
								{ key: "pending", label: "Pending Review" },
								{ key: "approved", label: "Approved" },
								{ key: "rejected", label: "Rejected" },
							].map((tab) => (
								<Button
									key={tab.key}
									onClick={() =>
										setFilter(
											tab.key as "all" | "pending" | "approved" | "rejected",
										)
									}
									size="sm"
									variant={filter === tab.key ? "default" : "outline"}
								>
									{tab.label}
									<Badge className="ml-2" variant="secondary">
										{
											qaItems.filter(
												(item) => tab.key === "all" || item.status === tab.key,
											).length
										}
									</Badge>
								</Button>
							))}
						</div>

						{/* Q&A List */}
						<div className="space-y-6">
							{isLoadingItems ? (
								<Card>
									<CardContent className="p-8 text-center">
										<Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
										<p className="text-muted-foreground">
											Loading questions...
										</p>
									</CardContent>
								</Card>
							) : error ? (
								<Card>
									<CardContent className="p-8 text-center">
										<XCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
										<p className="text-red-600 font-medium">
											Failed to load questions
										</p>
										<p className="text-sm text-muted-foreground mt-2">
											Please try refreshing the page
										</p>
									</CardContent>
								</Card>
							) : filteredItems.length > 0 ? (
								filteredItems.map((item) => (
									<Card className="relative" key={item.id}>
										<CardContent className="p-6">
											{/* Question */}
											<div className="flex items-start gap-3 mb-4">
												<div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
													<User className="h-4 w-4 text-blue-600" />
												</div>
												<div className="flex-1">
													<div className="flex items-center gap-2 mb-2">
														<span className="font-medium text-sm">
															{item.author}
														</span>
														<span className="text-xs text-muted-foreground">
															{new Date(item.timestamp).toLocaleString()}
														</span>
														<Badge className={getStatusColor(item.status)}>
															{getStatusIcon(item.status)}
															<span className="ml-1 capitalize">
																{item.status}
															</span>
														</Badge>
													</div>
													<p className="text-sm font-medium mb-2">
														{item.question}
													</p>
													<div className="flex gap-2">
														{item.repositories.map((repo) => (
															<Badge
																className="text-xs"
																key={repo}
																variant="outline"
															>
																{repo}
															</Badge>
														))}
													</div>
												</div>
											</div>

											<Separator className="my-4" />

											{/* Answer */}
											<div className="flex items-start gap-3">
												<div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100">
													<Bot className="h-4 w-4 text-green-600" />
												</div>
												<div className="flex-1">
													<div className="flex items-center gap-2 mb-2">
														<span className="font-medium text-sm">
															AI Assistant
														</span>
														<Badge className="text-xs" variant="secondary">
															Auto-generated
														</Badge>
													</div>
													<div className="prose prose-sm max-w-none">
														<p className="text-sm text-slate-700 whitespace-pre-wrap">
															{item.answer}
														</p>
													</div>
												</div>
											</div>

											{/* Actions */}
											<div className="flex items-center justify-between mt-4 pt-4 border-t">
												<div className="flex items-center gap-4">
													<div className="flex items-center space-x-2">
														<Button
															disabled={voteMutation.isPending}
															onClick={() => handleVote(item.id, "up")}
															size="sm"
															variant="ghost"
														>
															{voteMutation.isPending ? (
																<Loader2 className="mr-1 h-3 w-3 animate-spin" />
															) : (
																<ThumbsUp className="mr-1 h-3 w-3" />
															)}
															{item.upvotes}
														</Button>
														<Button
															disabled={voteMutation.isPending}
															onClick={() => handleVote(item.id, "down")}
															size="sm"
															variant="ghost"
														>
															{voteMutation.isPending ? (
																<Loader2 className="mr-1 h-3 w-3 animate-spin" />
															) : (
																<ThumbsDown className="mr-1 h-3 w-3" />
															)}
															{item.downvotes}
														</Button>
													</div>

													{item.status === "pending" && (
														<div className="flex gap-2">
															<Button
																className="h-8"
																disabled={updateStatusMutation.isPending}
																onClick={() =>
																	handleStatusUpdate(item.id, "approved")
																}
																size="sm"
																variant="outline"
															>
																{updateStatusMutation.isPending ? (
																	<Loader2 className="h-3 w-3 mr-1 animate-spin" />
																) : (
																	<CheckCircle className="h-3 w-3 mr-1" />
																)}
																Approve
															</Button>
															<Button
																className="h-8"
																disabled={updateStatusMutation.isPending}
																onClick={() =>
																	handleStatusUpdate(item.id, "rejected")
																}
																size="sm"
																variant="outline"
															>
																{updateStatusMutation.isPending ? (
																	<Loader2 className="h-3 w-3 mr-1 animate-spin" />
																) : (
																	<XCircle className="h-3 w-3 mr-1" />
																)}
																Reject
															</Button>
														</div>
													)}
												</div>

												{item.status === "approved" && (
													<div className="flex items-center space-x-2">
														<Checkbox
															checked={selectedForReport.includes(item.id)}
															id={`report-${item.id}`}
															onCheckedChange={() =>
																toggleReportSelection(item.id)
															}
														/>
														<Label
															className="text-xs"
															htmlFor={`report-${item.id}`}
														>
															Include in weekly report
														</Label>
													</div>
												)}
											</div>
										</CardContent>
									</Card>
								))
							) : (
								<Card>
									<CardContent className="p-8 text-center">
										<MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
										<p className="text-muted-foreground">
											{filter === "all"
												? "No questions asked yet"
												: `No ${filter} questions`}
										</p>
										<p className="text-sm text-muted-foreground mt-2">
											Start by asking a question about your repositories above
										</p>
									</CardContent>
								</Card>
							)}
						</div>
					</div>

					{/* Sidebar */}
					<div className="space-y-6">
						{/* Quick Stats */}
						<Card>
							<CardHeader>
								<CardTitle className="text-lg">Q&A Overview</CardTitle>
							</CardHeader>
							<CardContent className="space-y-4">
								<div className="flex justify-between items-center">
									<span className="text-sm text-muted-foreground">
										Total Questions
									</span>
									<Badge variant="secondary">{qaItems.length}</Badge>
								</div>
								<div className="flex justify-between items-center">
									<span className="text-sm text-muted-foreground">
										Pending Review
									</span>
									<Badge variant="outline">
										{qaItems.filter((item) => item.status === "pending").length}
									</Badge>
								</div>
								<div className="flex justify-between items-center">
									<span className="text-sm text-muted-foreground">
										Approved
									</span>
									<Badge className="bg-green-100 text-green-800">
										{
											qaItems.filter((item) => item.status === "approved")
												.length
										}
									</Badge>
								</div>
								<div className="flex justify-between items-center">
									<span className="text-sm text-muted-foreground">
										For Weekly Report
									</span>
									<Badge variant="secondary">{selectedForReport.length}</Badge>
								</div>
							</CardContent>
						</Card>

						{/* Example Questions */}
						<Card>
							<CardHeader>
								<CardTitle className="text-lg">Example Questions</CardTitle>
								<CardDescription>
									Get started with these sample questions
								</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-3">
									{[
										"What are the main performance bottlenecks in our API?",
										"Which components have the most technical debt?",
										"What security improvements were made last month?",
										"Which team members are most active in code reviews?",
										"What are the most common bug patterns?",
									].map((exampleQuestion) => (
										<Button
											className="w-full text-left justify-start h-auto p-3 text-xs"
											key={exampleQuestion}
											onClick={() => setQuestion(exampleQuestion)}
											size="sm"
											variant="ghost"
										>
											{exampleQuestion}
										</Button>
									))}
								</div>
							</CardContent>
						</Card>

						{/* Weekly Report Actions */}
						{selectedForReport.length > 0 && (
							<Card>
								<CardHeader>
									<CardTitle className="text-lg">Weekly Report</CardTitle>
									<CardDescription>
										{selectedForReport.length} Q&As selected
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="space-y-2">
										<Button className="w-full" size="sm">
											Generate Report Preview
										</Button>
										<Button className="w-full" size="sm" variant="outline">
											Export to Markdown
										</Button>
									</div>
								</CardContent>
							</Card>
						)}
					</div>
				</div>
			</main>
		</>
	);
}
