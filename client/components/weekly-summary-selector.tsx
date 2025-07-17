"use client";

import {
  AlertCircle,
  Calendar,
  Download,
  Eye,
  FileText,
  GitCommit,
  GitPullRequest,
  Loader2,
  MessageSquare,
  Plus,
  Send,
} from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useContributions, useUpdateContributions } from "@/lib/api/contributions";

interface SummaryItem {
  id: string;
  type: "commit" | "pr" | "issue" | "comment" | "qa";
  title: string;
  description: string;
  repository: string;
  author: string;
  date: string;
  url: string;
  status: "done" | "in-progress";
  selected: boolean;
}

interface WeeklySummarySelectorProps {
  userId: string;
}

const typeIcons = {
  comment: MessageSquare,
  commit: GitCommit,
  issue: AlertCircle,
  pr: GitPullRequest,
  qa: MessageSquare,
} as const;

const typeLabels = {
  comment: "Comment",
  commit: "Commit",
  issue: "Issue",
  pr: "Pull Request",
  qa: "Q&A",
} as const;

const statusColors = {
  all: "bg-gray-100 text-gray-800",
  done: "bg-green-100 text-green-800",
  "in-progress": "bg-blue-100 text-blue-800",
} as const;

type StateFilter = "all" | "done" | "in-progress";
type TypeFilter = "all" | "commit" | "pr" | "issue" | "qa";
export function WeeklySummarySelector({ userId }: WeeklySummarySelectorProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [filter, setFilter] = useState<StateFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [previewContent, setPreviewContent] = useState("");
  const [showPreview, setShowPreview] = useState(false);

  // Use the contributions API hooks
  const { data: contributionsData, isLoading } = useContributions(
    {
      pageable: {
        page: 0,
        size: 50,
        sort: ["createdAt,desc"],
      },
    },
    true,
  );

  const updateContributions = useUpdateContributions();

  // Helper functions for mapping types and statuses
  const mapContributionType = (type: string): "commit" | "pr" | "issue" | "comment" | "qa" => {
    if (type.includes("PullRequest")) return "pr";
    if (type.includes("Issue")) return "issue";
    if (type.includes("Commit")) return "commit";
    if (type.includes("Comment")) return "comment";
    return "commit";
  };

  const toggleItemSelection = (id: string) => {
    // Update the contribution selection status via API
    const contributionToUpdate = contributionsData?.content?.find(
      (contribution) => contribution.id === id,
    );

    if (contributionToUpdate) {
      const updatedContribution = {
        ...contributionToUpdate,
        isSelected: !contributionToUpdate.isSelected,
      };
      updateContributions.mutate([updatedContribution]);
    }
  };

  const selectAllByStatus = (_status: string) => {
    // All items are "done" status in current implementation
    // Update the contribution selection status via API for all items
    const contributionsToUpdate = contributionsData?.content?.map((contribution) => ({
      ...contribution,
      isSelected: true,
    }));

    if (contributionsToUpdate && contributionsToUpdate.length > 0) {
      updateContributions.mutate(contributionsToUpdate);
    }
  };

  const clearAllSelections = () => {
    // Update the contribution selection status via API for all items
    const contributionsToUpdate = contributionsData?.content?.map((contribution) => ({
      ...contribution,
      isSelected: false,
    }));

    if (contributionsToUpdate && contributionsToUpdate.length > 0) {
      updateContributions.mutate(contributionsToUpdate);
    }
  };

  const generatePreview = async () => {
    setIsGenerating(true);
    try {
      const selectedItems =
        contributionsData?.content
          ?.filter((contribution) => contribution.isSelected)
          .map((contribution) => ({
            author: contribution.username,
            date: contribution.createdAt || new Date().toISOString(),
            description: contribution.summary,
            id: contribution.id,
            repository: `repo-${contribution.gitRepositoryId}`,
            selected: contribution.isSelected,
            status: "done",
            title: contribution.summary,
            type: mapContributionType(contribution.type),
            url: "#",
          })) || [];
      const response = await fetch("/api/weekly-summary/generate", {
        body: JSON.stringify({
          items: selectedItems,
          userId,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewContent(data.summary);
        setShowPreview(true);
      }
    } catch (error) {
      console.error("Failed to generate preview:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const publishSummary = async () => {
    try {
      const selectedItems =
        contributionsData?.content
          ?.filter((contribution) => contribution.isSelected)
          .map((contribution) => ({
            author: contribution.username,
            date: contribution.createdAt || new Date().toISOString(),
            description: contribution.summary,
            id: contribution.id,
            repository: `repo-${contribution.gitRepositoryId}`,
            selected: contribution.isSelected,
            status: "done",
            title: contribution.summary,
            type: mapContributionType(contribution.type),
            url: "#",
          })) || [];
      const response = await fetch("/api/weekly-summary/publish", {
        body: JSON.stringify({
          items: selectedItems,
          summary: previewContent,
          userId,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });

      if (response.ok) {
        // Show success message or redirect
        console.log("Summary published successfully");
      }
    } catch (error) {
      console.error("Failed to publish summary:", error);
    }
  };

  const filteredItems =
    contributionsData?.content
      ?.map((contribution) => ({
        author: contribution.username,
        date: contribution.createdAt || new Date().toISOString(),
        description: contribution.summary,
        id: contribution.id,
        repository: `repo-${contribution.gitRepositoryId}`,
        selected: contribution.isSelected,
        status: "done" as StateFilter,
        title: contribution.summary,
        type: mapContributionType(contribution.type),
        url: "#",
      }))
      .filter((item) => {
        const statusMatch = filter === "all" || item.status === filter;
        const typeMatch = typeFilter === "all" || item.type === typeFilter;
        return statusMatch && typeMatch;
      }) || [];

  const selectedCount =
    contributionsData?.content?.filter((contribution) => contribution.isSelected).length || 0;
  const getTypeIcon = (type: SummaryItem["type"]) => {
    const Icon = typeIcons[type];
    return <Icon className="h-4 w-4" />;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Weekly Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span>Loading summary items...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Weekly Summary Builder
        </CardTitle>
        <CardDescription>
          Select changes and activities to include in next week's summary report
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-slate-50 rounded-lg">
              <div className="text-2xl font-bold text-slate-900">
                {contributionsData?.content?.length || 0}
              </div>
              <div className="text-xs text-slate-600">Total Items</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">
                {contributionsData?.content?.filter((item) => item.status === "done").length || 0}
              </div>
              <div className="text-xs text-green-600">Completed</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">
                {contributionsData?.content?.filter((item) => item.status === "in-progress")
                  .length || 0}
              </div>
              <div className="text-xs text-blue-600">In Progress</div>
            </div>
          </div>

          {/* Filters and Actions */}
          <div className="flex flex-wrap gap-2 items-center justify-between">
            <div className="flex gap-2">
              <Tabs onValueChange={(value) => setFilter(value as StateFilter)} value={filter}>
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="all">All</TabsTrigger>
                  <TabsTrigger value="done">Done</TabsTrigger>
                  <TabsTrigger value="in-progress">In Progress</TabsTrigger>
                </TabsList>
              </Tabs>

              <select
                className="px-3 py-1 border rounded-md text-sm"
                onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}
                value={typeFilter}
              >
                <option value="all">All Types</option>
                <option value="commit">Commits</option>
                <option value="pr">Pull Requests</option>
                <option value="issue">Issues</option>
                <option value="qa">Q&A</option>
              </select>
            </div>

            <div className="flex gap-2">
              <Button onClick={() => selectAllByStatus("done")} size="sm" variant="outline">
                <Plus className="h-3 w-3 mr-1" />
                Select All Done
              </Button>
              <Button onClick={clearAllSelections} size="sm" variant="outline">
                Clear All
              </Button>
            </div>
          </div>

          {/* Selected Items Summary */}
          {selectedCount > 0 && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-blue-900">{selectedCount} items selected</p>
                  <p className="text-sm text-blue-700">Ready to generate weekly summary</p>
                </div>
                <div className="flex gap-2">
                  <Button disabled={isGenerating} onClick={generatePreview} size="sm">
                    {isGenerating ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      <Eye className="h-3 w-3 mr-1" />
                    )}
                    Preview
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Items List */}
          <ScrollArea className="h-96">
            <div className="space-y-2">
              {filteredItems.length > 0 ? (
                filteredItems.map((item) => (
                  <div
                    className={`p-3 border rounded-lg transition-colors ${
                      item.selected ? "bg-blue-50 border-blue-200" : "bg-white hover:bg-slate-50"
                    }`}
                    key={item.id}
                  >
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={item.selected}
                        className="mt-1"
                        id={item.id}
                        onCheckedChange={() => toggleItemSelection(item.id)}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className="text-xs" variant="outline">
                            {getTypeIcon(item.type)}
                            <span className="ml-1">{typeLabels[item.type]}</span>
                          </Badge>
                          <Badge className={statusColors[item.status]} variant="secondary">
                            {item.status.replace("-", " ")}
                          </Badge>
                          <Badge className="text-xs" variant="outline">
                            {item.repository}
                          </Badge>
                        </div>
                        <Label className="font-medium text-sm cursor-pointer" htmlFor={item.id}>
                          {item.title}
                        </Label>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {item.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground mt-2">
                          <span>by {item.author}</span>
                          <span>{new Date(item.date).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No items found for the selected filters</p>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Action Buttons */}
          <Separator />
          <div className="flex gap-2 justify-end">
            <Dialog onOpenChange={setShowPreview} open={showPreview}>
              <DialogTrigger asChild>
                <Button disabled={selectedCount === 0} variant="outline">
                  <Eye className="h-4 w-4 mr-2" />
                  Preview Summary
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh]">
                <DialogHeader>
                  <DialogTitle>Weekly Summary Preview</DialogTitle>
                  <DialogDescription>
                    Review the generated summary before publishing to GitHub Wiki
                  </DialogDescription>
                </DialogHeader>
                <ScrollArea className="h-96 w-full">
                  <div className="prose prose-sm max-w-none p-4">
                    <pre className="whitespace-pre-wrap text-sm">{previewContent}</pre>
                  </div>
                </ScrollArea>
                <div className="flex gap-2 justify-end">
                  <Button onClick={() => setShowPreview(false)} variant="outline">
                    Close
                  </Button>
                  <Button onClick={publishSummary}>
                    <Send className="h-4 w-4 mr-2" />
                    Publish to Wiki
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Button disabled={selectedCount === 0} onClick={generatePreview}>
              <Download className="h-4 w-4 mr-2" />
              Generate Summary
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
