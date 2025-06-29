"use client";

import { Calendar, Clock, Download, FileText, Users } from "lucide-react";
import { Suspense } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { WeeklySummaryServer } from "@/components/weekly-summary-server";
import { useUser } from "@/contexts/user-context";

async function RecentSummaries() {
  // Simulate server-side data fetching
  await new Promise((resolve) => setTimeout(resolve, 800));

  const recentSummaries = [
    {
      date: "2024-01-12",
      id: "1",
      itemCount: 15,
      status: "published",
      title: "Weekly Summary - Jan 8-12, 2024",
    },
    {
      date: "2024-01-05",
      id: "2",
      itemCount: 12,
      status: "published",
      title: "Weekly Summary - Jan 1-5, 2024",
    },
    {
      date: "2023-12-29",
      id: "3",
      itemCount: 8,
      status: "draft",
      title: "Weekly Summary - Dec 25-29, 2023",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          <CardTitle className="text-lg">Recent Summaries</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recentSummaries.map((summary) => (
            <div
              className="flex items-center gap-3 p-3 border rounded-lg hover:bg-slate-50 transition-colors"
              key={summary.id}
            >
              <div className="flex h-8 w-8 items-center justify-center rounded bg-blue-100">
                <FileText className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{summary.title}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{summary.itemCount} items</span>
                  <span>•</span>
                  <span>{new Date(summary.date).toLocaleDateString()}</span>
                </div>
              </div>
              <Button size="sm" variant="ghost">
                <Download className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

async function QuickActions() {
  // Simulate server-side data fetching
  await new Promise((resolve) => setTimeout(resolve, 500));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full justify-start" variant="outline">
          <Clock className="h-4 w-4 mr-2" />
          Generate This Week's Summary
        </Button>
        <Button className="w-full justify-start" variant="outline">
          <Users className="h-4 w-4 mr-2" />
          Team Performance Report
        </Button>
        <Button className="w-full justify-start" variant="outline">
          <FileText className="h-4 w-4 mr-2" />
          Export All Summaries
        </Button>
        <Button className="w-full justify-start" variant="outline">
          <Calendar className="h-4 w-4 mr-2" />
          Schedule Auto-Summary
        </Button>
      </CardContent>
    </Card>
  );
}

export default function WeeklySummaryPage() {
  const { userId } = useUser();

  // Show not authenticated state if no userId
  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full text-center space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Authentication Required</h2>
            <p className="mt-2 text-sm text-gray-600">
              Please log in to access the weekly summary builder
            </p>
          </div>
          <div className="space-y-4">
            <Button className="w-full" onClick={() => (window.location.href = "/login")}>
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
          <div className="flex items-center gap-2">
            <Calendar className="h-6 w-6" />
            <h1 className="text-2xl font-bold">Weekly Summary Builder</h1>
          </div>
          <p className="text-slate-600">
            Create comprehensive weekly reports from your team's GitHub activity
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <WeeklySummaryServer userId={userId} />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Suspense
              fallback={
                <Card>
                  <CardHeader>
                    <div className="h-5 w-24 bg-slate-200 rounded animate-pulse" />
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div className="h-9 bg-slate-100 rounded animate-pulse" key={i} />
                    ))}
                  </CardContent>
                </Card>
              }
            >
              <QuickActions />
            </Suspense>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Summary Templates</CardTitle>
                <CardDescription>Choose from pre-built templates</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                    <p className="font-medium text-sm">Executive Summary</p>
                    <p className="text-xs text-muted-foreground">
                      High-level overview for leadership
                    </p>
                  </div>
                  <div className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                    <p className="font-medium text-sm">Technical Report</p>
                    <p className="text-xs text-muted-foreground">Detailed technical progress</p>
                  </div>
                  <div className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                    <p className="font-medium text-sm">Team Standup</p>
                    <p className="text-xs text-muted-foreground">Quick team update format</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Suspense
              fallback={
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      <div className="h-5 w-32 bg-slate-200 rounded animate-pulse" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <div className="flex items-center gap-3 p-2 border rounded" key={i}>
                          <div className="h-8 w-8 bg-slate-200 rounded animate-pulse" />
                          <div className="flex-1">
                            <div className="h-4 w-2/3 bg-slate-200 rounded animate-pulse mb-1" />
                            <div className="h-3 w-1/2 bg-slate-100 rounded animate-pulse" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              }
            >
              <RecentSummaries />
            </Suspense>
          </div>
        </div>
      </main>
    </>
  );
}
