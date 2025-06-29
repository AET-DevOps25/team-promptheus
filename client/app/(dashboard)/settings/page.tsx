import { Github, Settings, Zap } from "lucide-react";
import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

export default async function SettingsPage() {
  const userId = "abc";
  return (
    <>
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-2">
            <Settings className="h-6 w-6" />
            <h1 className="text-2xl font-bold">Settings - {userId}</h1>
          </div>
          <p className="text-slate-600">Configure your repositories and AI preferences</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-8">
          {/* Repository Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Github className="h-5 w-5" />
                Repository Configuration
              </CardTitle>
              <CardDescription>Select which repositories to monitor and analyze</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="repo-filter">Repository Filter</Label>
                <Input
                  defaultValue="my-org/*"
                  id="repo-filter"
                  placeholder="Enter repository names or patterns..."
                />
                <p className="text-xs text-muted-foreground">
                  Use wildcards (*) to match multiple repositories
                </p>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Monitoring Options</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="monitor-prs">Monitor Pull Requests</Label>
                      <p className="text-xs text-muted-foreground">
                        Track PR creation, reviews, and merges
                      </p>
                    </div>
                    <Switch defaultChecked id="monitor-prs" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="monitor-issues">Monitor Issues</Label>
                      <p className="text-xs text-muted-foreground">
                        Track issue creation and resolution
                      </p>
                    </div>
                    <Switch defaultChecked id="monitor-issues" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="monitor-commits">Monitor Commits</Label>
                      <p className="text-xs text-muted-foreground">
                        Analyze commit patterns and frequency
                      </p>
                    </div>
                    <Switch defaultChecked id="monitor-commits" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                AI Configuration
              </CardTitle>
              <CardDescription>Customize how AI analyzes and summarizes your data</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="auto-summaries">Automatic Weekly Summaries</Label>
                    <p className="text-xs text-muted-foreground">
                      Generate progress reports every Friday
                    </p>
                  </div>
                  <Switch defaultChecked id="auto-summaries" />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="semantic-search">Enhanced Semantic Search</Label>
                    <p className="text-xs text-muted-foreground">
                      Enable AI-powered code and issue search
                    </p>
                  </div>
                  <Switch defaultChecked id="semantic-search" />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="qa-mode">Interactive Q&A</Label>
                    <p className="text-xs text-muted-foreground">
                      Allow questions about repository content
                    </p>
                  </div>
                  <Switch defaultChecked id="qa-mode" />
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="summary-style">Summary Style</Label>
                <select className="w-full p-2 border rounded-md" id="summary-style">
                  <option value="detailed">Detailed (Technical focus)</option>
                  <option value="executive">Executive (High-level overview)</option>
                  <option value="developer">Developer (Code-focused)</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Save Settings */}
          <div className="flex justify-end gap-3">
            <Button variant="outline">Reset to Defaults</Button>
            <Button>Save Settings</Button>
          </div>
        </div>
      </main>
    </>
  );
}
