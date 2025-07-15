"use client";

import { BarChart3, Clock, GitBranch, Loader2, MessageSquare, Search, User } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { SearchModal } from "@/components/search-modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Markdown } from "@/components/ui/markdown";
import { WeeklySummaryServer } from "@/components/weekly-summary-server";
import { useUser } from "@/contexts/user-context";
import { useContributions } from "@/lib/api/contributions";
import { useGitRepoInformation } from "@/lib/api/server";

export default function DashboardPage() {
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const { userId } = useUser();

  // Fetch repository information
  const {
    data: repoData,
    isLoading: isRepoLoading,
    error: repoError,
  } = useGitRepoInformation(userId, !!userId);

  // Fetch contributions data
  const { isLoading: isContributionsLoading } = useContributions(
    {
      pageable: {
        page: 0,
        size: 100,
        sort: ["createdAt,desc"],
      },
    },
    !!userId,
  );

  const isLoading = isRepoLoading || isContributionsLoading;
  const hasRepoData = repoData && !repoError;

  // No stats calculation needed as it's not used in the component

  // Show not authenticated state if no userId
  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full text-center space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Authentication Required</h2>
            <p className="mt-2 text-sm text-gray-600">Please log in to access your dashboard</p>
          </div>
          <div className="space-y-4">
            <Button
              className="w-full"
              onClick={() => {
                window.location.href = "/login";
              }}
            >
              Go to Login
            </Button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <>
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Dashboard{userId ? ` - ${userId}` : ""}</h1>
              <div className="flex items-center gap-2 text-slate-600">
                <p>Your AI-powered GitHub insights</p>
                {hasRepoData && repoData?.repoLink && (
                  <>
                    <span>•</span>
                    <a
                      className="text-blue-600 hover:text-blue-800 underline"
                      href={repoData.repoLink}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      View Repository
                    </a>
                  </>
                )}
                {repoError && (
                  <>
                    <span>•</span>
                    <span className="text-amber-600 text-sm">
                      Repository not found or access denied
                    </span>
                  </>
                )}
              </div>
            </div>
            {hasRepoData && (
              <div className="text-right">
                <Badge variant={repoData.isMaintainer ? "default" : "secondary"}>
                  {repoData.isMaintainer ? "Maintainer" : "Viewer"}
                </Badge>
                <p className="text-xs text-muted-foreground mt-1">
                  Registered {new Date(repoData.createdAt).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Repository Info</CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading...</span>
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">
                    {hasRepoData ? repoData?.contents?.length || 0 : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {hasRepoData ? "Content items analyzed" : "Repository not available"}
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Questions Asked</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading...</span>
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">
                    {hasRepoData ? repoData?.questions?.length || 0 : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {hasRepoData ? "Total Q&A interactions" : "Repository not available"}
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Summaries</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading...</span>
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">
                    {hasRepoData ? repoData?.summaries?.length || 0 : "N/A"}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {hasRepoData ? "Generated insights" : "Repository not available"}
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Repository Status</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading...</span>
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{hasRepoData ? "Active" : "N/A"}</div>
                  <p className="text-xs text-muted-foreground">
                    {hasRepoData
                      ? repoData?.isMaintainer
                        ? "Maintainer access"
                        : "Viewer access"
                      : "Repository not available"}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-2">
          {/* Left Column */}
          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Quick Search
                </CardTitle>
                <CardDescription>
                  Find anything across your repositories with AI-powered semantic search
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <Button
                    className="flex-1 justify-start text-muted-foreground"
                    onClick={() => setIsSearchModalOpen(true)}
                    variant="outline"
                  >
                    <Search className="h-4 w-4 mr-2" />
                    Search commits, PRs, issues...
                    <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                      <span className="text-xs">⌘</span>K
                    </kbd>
                  </Button>
                </div>
                <SearchModal
                  isOpen={isSearchModalOpen}
                  onCloseAction={() => setIsSearchModalOpen(false)}
                  usercode={userId}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Recent Q&A
                </CardTitle>
                <CardDescription>
                  Latest questions and AI-powered answers about your repositories
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin" />
                      <span className="ml-2 text-sm text-muted-foreground">Loading Q&A...</span>
                    </div>
                  ) : hasRepoData && repoData?.questions && repoData.questions.length > 0 ? (
                    repoData.questions.slice(0, 3).map((qa) => (
                      <div
                        className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg"
                        key={qa.createdAt + qa.question}
                      >
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100">
                          <User className="h-3 w-3 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{qa.question}</p>
                          {qa.answers && qa.answers.length > 0 && (
                            <div className="mt-1">
                              <Markdown variant="compact">{qa.answers[0].answer.substring(0, 200) + (qa.answers[0].answer.length > 200 ? "..." : "")}</Markdown>
                            </div>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            <Badge className="text-xs" variant="secondary">
                              {qa.answers && qa.answers.length > 0 ? "Answered" : "Pending"}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {new Date(qa.createdAt).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">
                        {hasRepoData ? "No questions yet" : "Repository not available"}
                      </p>
                      <p className="text-xs">
                        {hasRepoData
                          ? "Ask your first question about the repository"
                          : "Check repository access or try a different user code"}
                      </p>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Button asChild className="flex-1" size="sm" variant="outline">
                      <Link href="/qa">View All Q&A</Link>
                    </Button>
                    <Button asChild className="flex-1" size="sm">
                      <Link href="/qa">Ask Question</Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>AI-generated summary of your repository</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <span className="ml-2 text-sm text-muted-foreground">Loading activity...</span>
                  </div>
                ) : hasRepoData && repoData?.summaries && repoData.summaries.length > 0 ? (
                  <div className="space-y-4">
                    {repoData.summaries.slice(0, 3).map((summary) => (
                      <div className="flex items-start gap-3" key={summary.id}>
                        <Badge variant="secondary">Summary</Badge>
                        <div>
                          <p className="font-medium">Repository Analysis</p>
                          <div className="mt-1">
                            <Markdown variant="compact">{summary.summary.substring(0, 120) + (summary.summary.length > 120 ? "..." : "")}</Markdown>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Generated on {new Date(summary.createdAt).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">
                      {hasRepoData ? "No activity summaries yet" : "Repository not available"}
                    </p>
                    <p className="text-xs">
                      {hasRepoData
                        ? "Repository analysis will appear here once available"
                        : "Check repository access or try a different user code"}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Weekly Summary */}
          <div>
            <WeeklySummaryServer userId={userId} />
          </div>
        </div>
      </main>
    </>
  );
}
