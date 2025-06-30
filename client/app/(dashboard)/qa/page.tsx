"use client";

import {
  Bot,
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useUser } from "@/contexts/user-context";
import { useCreateQuestion, useGitRepoInformation } from "@/lib/api/server";

type QAItem = {
  id: string;
  question: string;
  answer: string;
  author: string;
  timestamp: string;
  upvotes: number;
  downvotes: number;
  repositories: string[];
};

export default function QAPage() {
  const [question, setQuestion] = useState("");
  const [selectedForReport, setSelectedForReport] = useState<string[]>([]);

  const [votingStates, setVotingStates] = useState<
    Record<string, { isVoting: boolean; userVote: "up" | "down" | null }>
  >({});
  const [voteOptimisticUpdates, setVoteOptimisticUpdates] = useState<
    Record<string, { upvotes: number; downvotes: number }>
  >({});

  // Get user context for usercode
  const { userId } = useUser();

  // TanStack Query hooks
  const {
    data: repoData,
    isLoading: isLoadingItems,
    error,
  } = useGitRepoInformation(userId || "", !!userId);
  const createQuestionMutation = useCreateQuestion(userId || "");

  // Transform questions from GitRepoInformation to QAItem format
  const qaItems: QAItem[] =
    repoData?.questions?.map((q, index) => {
      const id = `q-${index}`;
      const optimisticUpdate = voteOptimisticUpdates[id];
      return {
        answer: q.answers?.[0]?.answer || "No answer yet",
        author: "User",
        downvotes: optimisticUpdate?.downvotes ?? Math.floor(Math.random() * 3),
        id,
        question: q.question,
        repositories: [repoData.repoLink.split("/").slice(-2).join("/")],
        timestamp: q.createdAt,

        upvotes: optimisticUpdate?.upvotes ?? Math.floor(Math.random() * 15) + 1,
      };
    }) || [];

  const handleSubmitQuestion = async () => {
    if (!question.trim() || !userId) return;

    try {
      await createQuestionMutation.mutateAsync({
        question: question.trim(),
      });
      setQuestion("");
    } catch (error) {
      console.error("Failed to submit question:", error);
    }
  };

  const handleVote = async (id: string, type: "up" | "down") => {
    // Get current item to calculate optimistic update
    const currentItem = qaItems.find((item) => item.id === id);
    if (!currentItem) return;

    const currentVotingState = votingStates[id] || { isVoting: false, userVote: null };

    // Prevent multiple votes while one is processing
    if (currentVotingState.isVoting) return;

    // Set voting state
    setVotingStates((prev) => ({
      ...prev,
      [id]: { isVoting: true, userVote: type },
    }));

    // Calculate optimistic update
    let newUpvotes = currentItem.upvotes;
    let newDownvotes = currentItem.downvotes;

    // Handle vote logic
    if (currentVotingState.userVote === type) {
      // User is removing their vote
      if (type === "up") newUpvotes--;
      else newDownvotes--;
    } else {
      // User is adding or changing their vote
      if (currentVotingState.userVote === "up") newUpvotes--;
      else if (currentVotingState.userVote === "down") newDownvotes--;

      if (type === "up") newUpvotes++;
      else newDownvotes++;
    }

    // Apply optimistic update
    setVoteOptimisticUpdates((prev) => ({
      ...prev,
      [id]: { downvotes: newDownvotes, upvotes: newUpvotes },
    }));

    try {
      // Simulate API call delay
      await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 400));

      // Simulate occasional API failure (5% chance)
      if (Math.random() < 0.05) {
        throw new Error("Voting failed");
      }

      // Update voting state with final result
      const finalUserVote = currentVotingState.userVote === type ? null : type;
      setVotingStates((prev) => ({
        ...prev,
        [id]: { isVoting: false, userVote: finalUserVote },
      }));
    } catch (error) {
      console.error("Voting failed:", error);

      // Revert optimistic update on failure
      setVoteOptimisticUpdates((prev) => ({
        ...prev,
        [id]: { downvotes: currentItem.downvotes, upvotes: currentItem.upvotes },
      }));

      // Reset voting state
      setVotingStates((prev) => ({
        ...prev,
        [id]: { isVoting: false, userVote: currentVotingState.userVote },
      }));
    }
  };

  const toggleReportSelection = (id: string) => {
    setSelectedForReport((prev) =>
      prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id],
    );
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
                  Ask anything about your repositories - code patterns, recent changes, team
                  activity, or technical decisions
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
                      AI will analyze your repositories to provide contextual answers
                    </p>
                    <Button
                      disabled={createQuestionMutation.isPending || !question.trim() || !userId}
                      onClick={handleSubmitQuestion}
                    >
                      {createQuestionMutation.isPending ? (
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

            {/* Q&A List */}
            <div className="space-y-6">
              {isLoadingItems ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                    <p className="text-muted-foreground">Loading questions...</p>
                  </CardContent>
                </Card>
              ) : error ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <XCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
                    <p className="text-red-600 font-medium">Failed to load questions</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Please try refreshing the page
                    </p>
                  </CardContent>
                </Card>
              ) : qaItems.length > 0 ? (
                qaItems.map((item) => (
                  <Card className="relative" key={item.id}>
                    <CardContent className="p-6">
                      {/* Question */}
                      <div className="flex items-start gap-3 mb-4">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
                          <User className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-sm">{item.author}</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(item.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm font-medium mb-2">{item.question}</p>
                          <div className="flex gap-2">
                            {item.repositories.map((repo) => (
                              <Badge className="text-xs" key={repo} variant="outline">
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
                            <span className="font-medium text-sm">AI Assistant</span>
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
                              disabled={votingStates[item.id]?.isVoting}
                              onClick={() => handleVote(item.id, "up")}
                              size="sm"
                              variant={
                                votingStates[item.id]?.userVote === "up" ? "default" : "ghost"
                              }
                            >
                              {votingStates[item.id]?.isVoting &&
                              votingStates[item.id]?.userVote === "up" ? (
                                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                              ) : (
                                <ThumbsUp className="mr-1 h-3 w-3" />
                              )}
                              {item.upvotes}
                            </Button>
                            <Button
                              disabled={votingStates[item.id]?.isVoting}
                              onClick={() => handleVote(item.id, "down")}
                              size="sm"
                              variant={
                                votingStates[item.id]?.userVote === "down" ? "default" : "ghost"
                              }
                            >
                              {votingStates[item.id]?.isVoting &&
                              votingStates[item.id]?.userVote === "down" ? (
                                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                              ) : (
                                <ThumbsDown className="mr-1 h-3 w-3" />
                              )}
                              {item.downvotes}
                            </Button>
                          </div>

                          {/* Status update buttons disabled for GitRepoInformation mode */}
                        </div>

                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={selectedForReport.includes(item.id)}
                            id={`report-${item.id}`}
                            onCheckedChange={() => toggleReportSelection(item.id)}
                          />
                          <Label className="text-xs" htmlFor={`report-${item.id}`}>
                            Include in weekly report
                          </Label>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No questions asked yet</p>
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
                  <span className="text-sm text-muted-foreground">Total Questions</span>
                  <Badge variant="secondary">{qaItems.length}</Badge>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">For Weekly Report</span>
                  <Badge variant="secondary">{selectedForReport.length}</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Example Questions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Example Questions</CardTitle>
                <CardDescription>Get started with these sample questions</CardDescription>
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
                  <CardDescription>{selectedForReport.length} Q&As selected</CardDescription>
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
