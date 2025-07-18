"use client";

import { AlertTriangle, Home, MessageSquare, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";

export default function QAError({
	error,
	reset,
}: {
	error: Error & { digest?: string };
	reset: () => void;
}) {
	useEffect(() => {
		console.error("Q&A error:", error);
	}, [error]);

	return (
		<>
			<header className="border-b bg-white">
				<div className="container mx-auto px-4 py-4">
					<div className="flex items-center gap-2">
						<MessageSquare className="h-6 w-6 text-red-600" />
						<h1 className="text-2xl font-bold text-red-600">Q&A Error</h1>
					</div>
					<p className="text-slate-600">
						Something went wrong with the Questions & Answers section
					</p>
				</div>
			</header>

			<main className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
				<Card className="w-full max-w-lg">
					<CardHeader className="text-center">
						<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
							<AlertTriangle className="h-6 w-6 text-red-600" />
						</div>
						<CardTitle className="text-xl">Q&A System Error</CardTitle>
						<CardDescription>
							We couldn't load the Questions & Answers section. This might be
							due to an AI service issue or a connection problem.
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						{process.env.NODE_ENV === "development" && (
							<div className="p-3 bg-red-50 border border-red-200 rounded-md">
								<p className="text-sm font-medium text-red-800 mb-1">
									Error Details:
								</p>
								<p className="text-xs text-red-700 font-mono break-all">
									{error.message}
								</p>
							</div>
						)}

						<div className="space-y-2">
							<Button className="w-full" onClick={reset}>
								<RefreshCw className="h-4 w-4 mr-2" />
								Retry Loading Q&A
							</Button>

							<div className="grid grid-cols-2 gap-2">
								<Button asChild variant="outline">
									<Link href="/dashboard">
										<Home className="h-4 w-4 mr-2" />
										Dashboard
									</Link>
								</Button>
								<Button asChild variant="outline">
									<Link href="/settings">Settings</Link>
								</Button>
							</div>
						</div>

						<div className="text-center pt-2 border-t">
							<p className="text-xs text-muted-foreground">
								The AI service might be temporarily unavailable. Please try
								again in a few moments.
							</p>
						</div>
					</CardContent>
				</Card>
			</main>
		</>
	);
}
