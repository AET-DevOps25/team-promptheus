"use client";

import {
	Bell,
	Database,
	Github,
	Save,
	Settings,
	Target,
	Zap,
} from "lucide-react";
import { useId } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export default function SettingsPage() {
	const repoFilterId = useId();
	const monitorPrsId = useId();
	const monitorIssuesId = useId();
	const monitorCommitsId = useId();
	const autoSummariesId = useId();
	const semanticSearchId = useId();
	const qaModeId = useId();
	const summaryStyleId = useId();

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
			<main className="container mx-auto px-4 py-8 max-w-4xl">
				<div className="space-y-8">
					{/* Header */}
					<div className="text-center space-y-4">
						<div className="flex items-center justify-center gap-2 mb-4">
							<Settings className="h-8 w-8 text-slate-600" />
							<h1 className="text-3xl font-bold text-slate-900">
								Repository Settings
							</h1>
						</div>
						<p className="text-slate-600 max-w-2xl mx-auto">
							Configure how Prompteus monitors your repositories and generates
							insights for your team.
						</p>
					</div>

					{/* Settings Cards */}
					<div className="grid gap-6 lg:grid-cols-1">
						{/* Repository Configuration */}
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Github className="h-5 w-5" />
									Repository Configuration
								</CardTitle>
								<CardDescription>
									Set up which repositories to monitor and how to connect to
									them.
								</CardDescription>
							</CardHeader>
							<CardContent className="space-y-6">
								<div className="space-y-2">
									<Label htmlFor={repoFilterId}>Repository Filter</Label>
									<Input
										defaultValue="my-org/*"
										id={repoFilterId}
										placeholder="Enter repository names or patterns..."
									/>
									<p className="text-xs text-muted-foreground">
										Use wildcards (*) to match multiple repositories
									</p>
								</div>

								<div className="space-y-4">
									<h4 className="font-medium flex items-center gap-2">
										<Target className="h-4 w-4" />
										Monitoring Scope
									</h4>
									<div className="space-y-3">
										<div className="flex items-center justify-between">
											<div className="space-y-1">
												<p className="text-sm font-medium">Pull Requests</p>
												<p className="text-xs text-muted-foreground">
													Monitor PR creation, reviews, and merges
												</p>
											</div>
											<Switch defaultChecked id={monitorPrsId} />
										</div>
										<div className="flex items-center justify-between">
											<div className="space-y-1">
												<p className="text-sm font-medium">Issues</p>
												<p className="text-xs text-muted-foreground">
													Track issue creation and resolution
												</p>
											</div>
											<Switch defaultChecked id={monitorIssuesId} />
										</div>
										<div className="flex items-center justify-between">
											<div className="space-y-1">
												<p className="text-sm font-medium">Commits</p>
												<p className="text-xs text-muted-foreground">
													Monitor code commits and changes
												</p>
											</div>
											<Switch defaultChecked id={monitorCommitsId} />
										</div>
									</div>
								</div>
							</CardContent>
						</Card>

						{/* AI Features */}
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Zap className="h-5 w-5" />
									AI-Powered Features
									<Badge
										className="bg-purple-100 text-purple-800"
										variant="secondary"
									>
										Beta
									</Badge>
								</CardTitle>
								<CardDescription>
									Configure AI features for automated insights and assistance.
								</CardDescription>
							</CardHeader>
							<CardContent className="space-y-6">
								<div className="space-y-3">
									<div className="flex items-center justify-between">
										<div className="space-y-1">
											<p className="text-sm font-medium">Automatic Summaries</p>
											<p className="text-xs text-muted-foreground">
												Generate weekly summaries of repository activity
											</p>
										</div>
										<Switch defaultChecked id={autoSummariesId} />
									</div>
									<div className="flex items-center justify-between">
										<div className="space-y-1">
											<p className="text-sm font-medium">Semantic Search</p>
											<p className="text-xs text-muted-foreground">
												Enable AI-powered search across code and discussions
											</p>
										</div>
										<Switch defaultChecked id={semanticSearchId} />
									</div>
									<div className="flex items-center justify-between">
										<div className="space-y-1">
											<p className="text-sm font-medium">Q&A Mode</p>
											<p className="text-xs text-muted-foreground">
												Allow team members to ask questions about the codebase
											</p>
										</div>
										<Switch defaultChecked id={qaModeId} />
									</div>
								</div>

								<div className="space-y-2">
									<Label htmlFor={summaryStyleId}>Summary Style</Label>
									<select
										className="w-full p-2 border rounded-md"
										id={summaryStyleId}
									>
										<option value="detailed">Detailed (Technical focus)</option>
										<option value="executive">
											Executive (High-level overview)
										</option>
										<option value="balanced">Balanced (Mixed audience)</option>
									</select>
								</div>
							</CardContent>
						</Card>

						{/* Notifications */}
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Bell className="h-5 w-5" />
									Notifications
								</CardTitle>
								<CardDescription>
									Configure when and how you want to be notified about
									repository activities.
								</CardDescription>
							</CardHeader>
							<CardContent className="space-y-4">
								<div className="bg-slate-50 p-4 rounded-lg">
									<p className="text-sm text-slate-600">
										🚧 Notification settings will be available in the next
										release. Currently, summaries are generated automatically
										and accessible through the dashboard.
									</p>
								</div>
							</CardContent>
						</Card>

						{/* Data & Privacy */}
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<Database className="h-5 w-5" />
									Data & Privacy
								</CardTitle>
								<CardDescription>
									Manage how your data is processed and stored.
								</CardDescription>
							</CardHeader>
							<CardContent className="space-y-4">
								<div className="space-y-3">
									<div className="bg-green-50 p-4 rounded-lg">
										<h4 className="font-medium text-green-900 mb-2">
											🔒 Privacy-First Approach
										</h4>
										<ul className="text-sm text-green-800 space-y-1">
											<li>
												• Repository data is processed but not permanently
												stored
											</li>
											<li>• Only metadata and summaries are retained</li>
											<li>
												• All data processing happens within secure environments
											</li>
											<li>
												• You maintain full control over your GitHub access
												tokens
											</li>
										</ul>
									</div>

									<div className="bg-blue-50 p-4 rounded-lg">
										<h4 className="font-medium text-blue-900 mb-2">
											📊 Data Usage
										</h4>
										<ul className="text-sm text-blue-800 space-y-1">
											<li>
												• Code content is analyzed for insights but not stored
											</li>
											<li>
												• Commit messages and PR descriptions are processed for
												summaries
											</li>
											<li>
												• User activity patterns help generate personalized
												insights
											</li>
											<li>
												• No personal code is shared outside your organization
											</li>
										</ul>
									</div>
								</div>
							</CardContent>
						</Card>
					</div>

					{/* Save Button */}
					<div className="flex justify-center pt-6">
						<Button className="w-full max-w-md" size="lg">
							<Save className="h-4 w-4 mr-2" />
							Save Settings
						</Button>
					</div>
				</div>
			</main>
		</div>
	);
}
