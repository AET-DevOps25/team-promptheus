"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn, Link as LinkIcon, Copy, Check } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUser } from "@/contexts/user-context";

export default function LoginLandingPage() {
	const [userCode, setUserCode] = useState("");
	const [copied, setCopied] = useState(false);
	const router = useRouter();
	const { userId, isAuthenticated } = useUser();

	const handleLogin = () => {
		if (userCode.trim()) {
			router.push(`/login/${encodeURIComponent(userCode.trim())}`);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === "Enter") {
			handleLogin();
		}
	};

	const exampleUrl = `${typeof window !== "undefined" ? window.location.origin : ""}/login/your-user-code`;

	const copyToClipboard = async () => {
		try {
			await navigator.clipboard.writeText(exampleUrl);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch (err) {
			console.error("Failed to copy:", err);
		}
	};

	return (
		<div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
			<div className="max-w-2xl w-full space-y-8">
				<div className="text-center">
					<LogIn className="mx-auto h-12 w-12 text-blue-600" />
					<h2 className="mt-6 text-3xl font-extrabold text-gray-900">
						Access Your Repository Dashboard
					</h2>
					<p className="mt-2 text-sm text-gray-600">
						Enter your user code or use a direct login URL to access your personalized dashboard
					</p>
				</div>

				{/* Current Status */}
				{isAuthenticated && (
					<Card className="border-green-200 bg-green-50">
						<CardContent className="pt-6">
							<div className="flex items-center gap-2 text-green-800">
								<Check className="h-5 w-5" />
								<span className="font-medium">Already logged in as: {userId}</span>
							</div>
							<Button
								onClick={() => router.push("/dashboard")}
								className="mt-3 w-full"
							>
								Go to Dashboard
							</Button>
						</CardContent>
					</Card>
				)}

				{/* Manual Login */}
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<LogIn className="h-5 w-5" />
							Quick Login
						</CardTitle>
						<CardDescription>
							Enter your user code to access your repository dashboard
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="space-y-2">
							<Label htmlFor="usercode">User Code / Repository ID</Label>
							<Input
								id="usercode"
								value={userCode}
								onChange={(e) => setUserCode(e.target.value)}
								onKeyPress={handleKeyPress}
								placeholder="Enter your user code here..."
								className="text-center"
							/>
						</div>
						<Button
							onClick={handleLogin}
							disabled={!userCode.trim()}
							className="w-full"
						>
							Login with User Code
						</Button>
					</CardContent>
				</Card>

				{/* URL-based Login Instructions */}
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<LinkIcon className="h-5 w-5" />
							Direct URL Access
						</CardTitle>
						<CardDescription>
							Use a direct URL to automatically log in users
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="space-y-2">
							<Label>URL Format</Label>
							<div className="flex items-center gap-2">
								<Input
									value={exampleUrl}
									readOnly
									className="font-mono text-sm"
								/>
								<Button
									variant="outline"
									size="sm"
									onClick={copyToClipboard}
									className="flex items-center gap-1"
								>
									{copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
									{copied ? "Copied!" : "Copy"}
								</Button>
							</div>
							<p className="text-xs text-gray-500">
								Replace "your-user-code" with the actual user code
							</p>
						</div>

						<div className="bg-blue-50 p-4 rounded-lg">
							<h4 className="font-medium text-blue-900 mb-2">How it works:</h4>
							<ul className="text-sm text-blue-800 space-y-1">
								<li>• Users visit a URL with their unique code</li>
								<li>• The system automatically sets their session</li>
								<li>• They're redirected to their personalized dashboard</li>
								<li>• No manual login required</li>
							</ul>
						</div>

						<div className="bg-amber-50 p-4 rounded-lg">
							<h4 className="font-medium text-amber-900 mb-2">Example URLs:</h4>
							<div className="text-sm text-amber-800 space-y-1 font-mono">
								<div>/login/user123</div>
								<div>/login/repo-abc-xyz</div>
								<div>/login/team-project-alpha</div>
							</div>
						</div>
					</CardContent>
				</Card>

				{/* Additional Info */}
				<div className="text-center">
					<p className="text-xs text-gray-500">
						Need help? Contact your administrator or check the documentation for your specific user code.
					</p>
				</div>
			</div>
		</div>
	);
}
