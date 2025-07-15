"use client";

import {
  Calendar,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Filter,
  GitCommit,
  GitPullRequest,
  MessageSquare,
  RefreshCw,
  Square,
  User,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useUser } from "@/contexts/user-context";
import {
  type ContributionDto,
  useContributions,
  useUpdateContributions,
  useTriggerContributionFetch,
} from "@/lib/api/contributions";

// Helper function to get week range based on week offset (0 = current week, -1 = last week, etc.)
function getWeekRange(weekOffset = 0) {
  const now = new Date();
  const startOfWeek = new Date(now);
  const day = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
  const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is sunday
  startOfWeek.setDate(diff + (weekOffset * 7));
  startOfWeek.setHours(0, 0, 0, 0);

  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999);

  return {
    startDate: startOfWeek.toISOString(), // Full ISO string for API
    endDate: endOfWeek.toISOString(), // Full ISO string for API
    weekLabel: getWeekLabel(startOfWeek, endOfWeek, weekOffset),
  };
}

// Helper function to generate week label
function getWeekLabel(startDate: Date, endDate: Date, weekOffset: number): string {
  if (weekOffset === 0) return "This Week";
  if (weekOffset === -1) return "Last Week";
  if (weekOffset > 0) return `${weekOffset} Week${weekOffset > 1 ? 's' : ''} Ahead`;
  return `${Math.abs(weekOffset)} Week${Math.abs(weekOffset) > 1 ? 's' : ''} Ago`;
}

// Type icons mapping
const typeIcons = {
  commit: GitCommit,
  pullrequest: GitPullRequest,
  issue: MessageSquare,
  comment: MessageSquare,
} as const;

// Type labels mapping
const typeLabels = {
  commit: "Commit",
  pullrequest: "Pull Request",
  issue: "Issue",
  comment: "Comment",
} as const;

export default function DeveloperPage() {
  const { userId } = useUser();
  const [selectedUser, setSelectedUser] = useState<string>("all");
  const [weekOffset, setWeekOffset] = useState(0); // 0 = current week, -1 = last week, etc.
  const weekRange = getWeekRange(weekOffset);

  // Fetch contributions for current week
  const {
    data: contributionsData,
    isLoading,
    error,
  } = useContributions(
    {
      startDate: weekRange.startDate,
      endDate: weekRange.endDate,
      contributor: selectedUser === "all" ? undefined : selectedUser,
      pageable: {
        page: 0,
        size: 100,
        sort: ["createdAt,desc"],
      },
    },
    !!userId, // Enable query when userId exists
  );

  const updateContributions = useUpdateContributions();
  const triggerFetch = useTriggerContributionFetch();

  // Extract contributions from the API response
  const contributions = useMemo(() => {
    if (!contributionsData?.content) return [];
    // Handle the API response structure - content might be an array of unknown objects
    const content = contributionsData.content;
    if (Array.isArray(content)) {
      return content as ContributionDto[];
    }
    return [];
  }, [contributionsData]);

  // Fetch all contributions to get unique users (without user filter)
  const {
    data: allContributionsData,
  } = useContributions(
    {
      startDate: weekRange.startDate,
      endDate: weekRange.endDate,
      pageable: {
        page: 0,
        size: 1000, // Get more to see all users
        sort: ["createdAt,desc"],
      },
    },
    !!userId,
  );

  // Get unique users from all contributions
  const uniqueUsers = useMemo(() => {
    if (!allContributionsData?.content) return [];
    const content = allContributionsData.content;
    if (Array.isArray(content)) {
      const allContribs = content as ContributionDto[];
      const users = new Set(allContribs.map((contrib) => contrib.username));
      return Array.from(users).sort();
    }
    return [];
  }, [allContributionsData]);


  // Handle individual contribution selection
  const handleContributionToggle = (contribution: ContributionDto) => {
    // Send only the changed contribution
    const updatedContribution = {
      ...contribution,
      isSelected: !contribution.isSelected,
    };
    updateContributions.mutate([updatedContribution]);
  };

  // Handle select all / deselect all
  const handleSelectAll = (selected: boolean) => {
    // Send all contributions with the new selection state
    const updatedContributions = contributions.map((contrib) => ({
      ...contrib,
      isSelected: selected,
    }));
    updateContributions.mutate(updatedContributions);
  };

  // Calculate selection stats
  const selectedCount = contributions.filter((contrib) => contrib.isSelected).length;
  const totalCount = contributions.length;

  // Show authentication required if no user
  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full text-center space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Authentication Required</h2>
            <p className="mt-2 text-sm text-gray-600">
              Please log in to access the developer view
            </p>
          </div>
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
    );
  }

  return (
    <>
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <User className="h-6 w-6" />
              <h1 className="text-2xl font-bold">Developer View</h1>
            </div>
            <div className="flex items-center gap-4">
              {/* Week Selector */}
              <div className="flex items-center gap-2 border rounded-lg p-2 bg-white">
                <Button
                  onClick={() => setWeekOffset(weekOffset - 1)}
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <div className="flex flex-col items-center min-w-[140px]">
                  <Badge variant="outline" className="mb-1">
                    {weekRange.weekLabel}
                  </Badge>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    <span>
                      {new Date(weekRange.startDate).toLocaleDateString()} -{" "}
                      {new Date(weekRange.endDate).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <Button
                  onClick={() => setWeekOffset(weekOffset + 1)}
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Quick Week Presets */}
              <div className="flex items-center gap-1">
                <Button
                  onClick={() => setWeekOffset(0)}
                  size="sm"
                  variant={weekOffset === 0 ? "default" : "outline"}
                  className="text-xs px-2"
                >
                  This Week
                </Button>
                <Button
                  onClick={() => setWeekOffset(-1)}
                  size="sm"
                  variant={weekOffset === -1 ? "default" : "outline"}
                  className="text-xs px-2"
                >
                  Last Week
                </Button>
              </div>

              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4" />
                <Select value={selectedUser} onValueChange={setSelectedUser}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by user" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Users</SelectItem>
                    {uniqueUsers.map((user) => (
                      <SelectItem key={user} value={user}>
                        {user}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={() => triggerFetch.mutate()}
                size="sm"
                variant="outline"
                disabled={triggerFetch.isPending}
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${triggerFetch.isPending ? "animate-spin" : ""}`} />
                {triggerFetch.isPending ? "Fetching..." : "Refresh Data"}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Contributions - {weekRange.weekLabel}</span>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => handleSelectAll(true)}
                    size="sm"
                    variant="outline"
                    disabled={updateContributions.isPending}
                  >
                    <CheckSquare className="h-4 w-4 mr-1" />
                    {updateContributions.isPending ? "Saving..." : "Select All"}
                  </Button>
                  <Button
                    onClick={() => handleSelectAll(false)}
                    size="sm"
                    variant="outline"
                    disabled={updateContributions.isPending}
                  >
                    <Square className="h-4 w-4 mr-1" />
                    {updateContributions.isPending ? "Saving..." : "Deselect All"}
                  </Button>
                </div>
              </CardTitle>
              <CardDescription>
                Select contributions to include in your summary for {weekRange.weekLabel.toLowerCase()}.
                {selectedCount > 0 && (
                  <span className="font-medium text-primary ml-1">
                    {selectedCount} of {totalCount} selected
                  </span>
                )}
                {updateContributions.isPending && (
                  <span className="text-orange-600 ml-2">
                    ⏳ Saving changes...
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="text-center py-8 text-red-600">
                  <p>Error loading contributions: {error.message}</p>
                </div>
              )}

              {isLoading && (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Loading contributions...</p>
                </div>
              )}

              {!isLoading && !error && contributions.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No contributions found for {weekRange.weekLabel.toLowerCase()}.</p>
                  <div className="flex flex-col gap-1 mt-2">
                    {selectedUser !== "all" && (
                      <p className="text-sm">Try changing the user filter.</p>
                    )}
                    <p className="text-sm">Try selecting a different week or refreshing the data.</p>
                  </div>
                  <p className="text-xs mt-2 text-muted-foreground">
                    Searching {weekRange.weekLabel.toLowerCase()} ({new Date(weekRange.startDate).toLocaleDateString()} to{" "}
                    {new Date(weekRange.endDate).toLocaleDateString()})
                    {selectedUser !== "all" && ` for user: ${selectedUser}`}
                  </p>
                </div>
              )}

              {!isLoading && !error && contributions.length > 0 && (
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">
                          <Checkbox
                            checked={selectedCount === totalCount && totalCount > 0}
                            onCheckedChange={(checked) => handleSelectAll(!!checked)}
                            disabled={updateContributions.isPending}
                          />
                        </TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Summary</TableHead>
                        <TableHead>Author</TableHead>
                        <TableHead>Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {contributions.map((contribution) => {
                        const typeKey = contribution.type.toLowerCase() as keyof typeof typeIcons;
                        const Icon = typeIcons[typeKey] || GitCommit;
                        const label = typeLabels[typeKey] || contribution.type;

                        return (
                          <TableRow
                            key={contribution.id}
                            className={contribution.isSelected ? "bg-blue-50" : ""}
                          >
                            <TableCell>
                              <Checkbox
                                checked={contribution.isSelected}
                                onCheckedChange={() => handleContributionToggle(contribution)}
                                disabled={updateContributions.isPending}
                              />
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Icon className="h-4 w-4 text-muted-foreground" />
                                <Badge variant="secondary" className="text-xs">
                                  {label}
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell className="max-w-md">
                              <div className="truncate" title={contribution.summary}>
                                {contribution.summary}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <User className="h-4 w-4 text-muted-foreground" />
                                {contribution.username}
                              </div>
                            </TableCell>
                            <TableCell>
                              {contribution.createdAt
                                ? new Date(contribution.createdAt).toLocaleDateString()
                                : "Unknown"}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  );
}
