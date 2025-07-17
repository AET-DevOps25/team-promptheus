"use client";

import { AlertTriangle, Home, RefreshCw } from "lucide-react";
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

export default function ErrorPage({
	error,
	reset,
}: {
	error: Error & { digest?: string };
	reset: () => void;
}) {
	useEffect(() => {
		// Log the error to an error reporting service
		console.error("Application error:", error);
	}, [error]);

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
			<Card className="w-full max-w-md">
				<CardHeader className="text-center">
					<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
						<AlertTriangle className="h-6 w-6 text-red-600" />
					</div>
					<CardTitle className="text-2xl">Something went wrong!</CardTitle>
					<CardDescription>
						We encountered an unexpected error. This has been logged and we'll
						look into it.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					{process.env.NODE_ENV === "development" && (
						<div className="p-3 bg-red-50 border border-red-200 rounded-md">
							<p className="text-sm font-medium text-red-800 mb-1">
								Error Details:
							</p>
							<p className="text-xs text-red-700 font-mono">{error.message}</p>
							{error.digest && (
								<p className="text-xs text-red-600 mt-1">
									Error ID: {error.digest}
								</p>
							)}
						</div>
					)}

					<div className="flex gap-2">
						<Button className="flex-1" onClick={reset}>
							<RefreshCw className="h-4 w-4 mr-2" />
							Try Again
						</Button>
						<Button asChild className="flex-1" variant="outline">
							<Link href="/">
								<Home className="h-4 w-4 mr-2" />
								Go Home
							</Link>
						</Button>
					</div>

					<div className="text-center">
						<p className="text-xs text-muted-foreground">
							If this problem persists, please contact support with the error ID
							above.
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	);
}
