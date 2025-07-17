"use client";

import { ArrowLeft, Bug, Calendar, GitCommit, GitPullRequest, Package, Users } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Markdown } from "@/components/ui/markdown";
import { QuestionAnswerSection } from "@/components/ui/question-answer";
import { Skeleton } from "@/components/ui/skeleton";
import { useUser } from "@/contexts/user-context";
import { useCreateQuestion, useQueryClient, useQuestionsAndAnswers, useSummaries } from "@/lib/api";

function SummaryLoading() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="flex-1">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Array.from({ length: 5 }, () => crypto.randomUUID()).map((uuid) => (
            <Card key={uuid}>
              <CardContent className="p-4 text-center">
                <Skeleton className="h-8 w-12 mx-auto mb-2" />
                <Skeleton className="h-4 w-16 mx-auto" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Content sections */}
        {Array.from({ length: 4 }, () => crypto.randomUUID()).map((uuid) => (
          <Card key={uuid}>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default function SingleSummaryPage() {
  const params = useParams();
  const router = useRouter();
  const summaryId = params.id as string;

  // Get user context for usercode
  const { userId } = useUser();

  // Fetch all summaries and find the one with matching ID
  const { data: summaries, isLoading, error } = useSummaries();

  // Get the summary data
  const summary = summaries?.find((s) => s.id?.toString() === summaryId);

  // Fetch Q&A data if we have the summary
  const { data: questionsAndAnswers, isLoading: qaLoading } = useQuestionsAndAnswers(
    summary?.username || "",
    summary?.week || "",
    !!summary?.username && !!summary?.week,
  );

  // Question submission mutation
  const createQuestionMutation = useCreateQuestion(userId || "");
  const queryClient = useQueryClient();

  const handleSubmitQuestion = async (question: string) => {
    if (!userId || !summary?.username) return;

    try {
      await createQuestionMutation.mutateAsync({
        gitRepositoryId: summary.gitRepositoryId,
        question,
        username: summary.username,
        weekId: summary.week,
      });
      // Manually invalidate the Q&A queries for this specific user/week
      if (summary.week) {
        queryClient.invalidateQueries({
          queryKey: ["server", "qa", summary.username, summary.week],
        });
      }
    } catch (error) {
      console.error("Failed to submit question:", error);
    }
  };

  if (isLoading) {
    return <SummaryLoading />;
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Summary</h2>
          <p className="text-gray-600 mb-4">There was an error loading the summary.</p>
          <Button onClick={() => router.back()}>Go Back</Button>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Summary Not Found</h2>
          <p className="text-gray-600 mb-4">The requested summary could not be found.</p>
          <Button onClick={() => router.back()}>Go Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button onClick={() => router.back()} size="icon" variant="ghost">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold">{summary.username}'s Summary</h1>
              <Badge variant="secondary">{summary.week}</Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>
                Generated on{" "}
                {summary.createdAt
                  ? new Date(summary.createdAt).toLocaleDateString()
                  : "Unknown date"}
              </span>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <div className="p-2 bg-blue-100 rounded-full">
                  <GitCommit className="h-4 w-4 text-blue-600" />
                </div>
              </div>
              <div className="text-2xl font-bold">{summary.commitsCount || 0}</div>
              <div className="text-xs text-muted-foreground">Commits</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <div className="p-2 bg-green-100 rounded-full">
                  <GitPullRequest className="h-4 w-4 text-green-600" />
                </div>
              </div>
              <div className="text-2xl font-bold">{summary.pullRequestsCount || 0}</div>
              <div className="text-xs text-muted-foreground">Pull Requests</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <div className="p-2 bg-orange-100 rounded-full">
                  <Bug className="h-4 w-4 text-orange-600" />
                </div>
              </div>
              <div className="text-2xl font-bold">{summary.issuesCount || 0}</div>
              <div className="text-xs text-muted-foreground">Issues</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <div className="p-2 bg-purple-100 rounded-full">
                  <Package className="h-4 w-4 text-purple-600" />
                </div>
              </div>
              <div className="text-2xl font-bold">{summary.releasesCount || 0}</div>
              <div className="text-xs text-muted-foreground">Releases</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 text-center">
              <div className="flex items-center justify-center mb-2">
                <div className="p-2 bg-indigo-100 rounded-full">
                  <Users className="h-4 w-4 text-indigo-600" />
                </div>
              </div>
              <div className="text-2xl font-bold">{summary.totalContributions || 0}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </CardContent>
          </Card>
        </div>

        {/* Overview */}
        {summary.overview && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 bg-blue-100 rounded-full">
                  <Calendar className="h-4 w-4 text-blue-600" />
                </div>
                Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Markdown variant="default">{summary.overview}</Markdown>
            </CardContent>
          </Card>
        )}

        {/* Activity Summaries */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Commits */}
          {summary.commitsSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <GitCommit className="h-5 w-5 text-blue-600" />
                  Commits
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Markdown variant="default">{summary.commitsSummary}</Markdown>
              </CardContent>
            </Card>
          )}

          {/* Pull Requests */}
          {summary.pullRequestsSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <GitPullRequest className="h-5 w-5 text-green-600" />
                  Pull Requests
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Markdown variant="default">{summary.pullRequestsSummary}</Markdown>
              </CardContent>
            </Card>
          )}

          {/* Issues */}
          {summary.issuesSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Bug className="h-5 w-5 text-orange-600" />
                  Issues
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Markdown variant="default">{summary.issuesSummary}</Markdown>
              </CardContent>
            </Card>
          )}

          {/* Releases */}
          {summary.releasesSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Package className="h-5 w-5 text-purple-600" />
                  Releases
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Markdown variant="default">{summary.releasesSummary}</Markdown>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Analysis */}
        {summary.analysis && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 bg-indigo-100 rounded-full">
                  <Users className="h-4 w-4 text-indigo-600" />
                </div>
                Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Markdown variant="default">{summary.analysis}</Markdown>
            </CardContent>
          </Card>
        )}

        {/* Key Achievements and Areas for Improvement */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Key Achievements */}
          {summary.keyAchievements && summary.keyAchievements.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg text-green-700">
                  ✨ Key Achievements
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {summary.keyAchievements.map((achievement) => (
                    <li
                      className="flex items-start gap-2"
                      key={`achievement-${achievement.slice(0, 50).replace(/\s+/g, "-")}`}
                    >
                      <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                      <div className="flex-1">
                        <Markdown variant="compact">{achievement}</Markdown>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Areas for Improvement */}
          {summary.areasForImprovement && summary.areasForImprovement.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg text-orange-700">
                  🎯 Areas for Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {summary.areasForImprovement.map((area) => (
                    <li
                      className="flex items-start gap-2"
                      key={`improvement-${area.slice(0, 50).replace(/\s+/g, "-")}`}
                    >
                      <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                      <div className="flex-1">
                        <Markdown variant="compact">{area}</Markdown>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Q&A Section - Moved to bottom */}
        <QuestionAnswerSection
          isLoading={qaLoading}
          isSubmitting={createQuestionMutation.isPending}
          onSubmitQuestion={userId ? handleSubmitQuestion : undefined}
          questionsAndAnswers={questionsAndAnswers || []}
          username={summary.username}
          weekId={summary.week}
        />
      </div>
    </div>
  );
}
