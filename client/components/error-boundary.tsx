"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import type { ComponentType, ErrorInfo, ReactNode } from "react";
import React, { Component, useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";

interface ErrorBoundaryState {
	hasError: boolean;
	error?: Error;
}

interface ErrorBoundaryProps {
	children: ReactNode;
	fallback?: ComponentType<{ error?: Error; reset: () => void }>;
}

export class ErrorBoundary extends Component<
	ErrorBoundaryProps,
	ErrorBoundaryState
> {
	constructor(props: ErrorBoundaryProps) {
		super(props);
		this.state = { hasError: false };
	}

	static getDerivedStateFromError(error: Error): ErrorBoundaryState {
		return { error, hasError: true };
	}

	componentDidCatch(error: Error, errorInfo: ErrorInfo) {
		console.error("ErrorBoundary caught an error:", error, errorInfo);
	}

	render() {
		if (this.state.hasError) {
			const reset = () => {
				this.setState({ error: undefined, hasError: false });
			};

			if (this.props.fallback) {
				const FallbackComponent = this.props.fallback;
				return <FallbackComponent error={this.state.error} reset={reset} />;
			}

			return (
				<Card className="w-full max-w-md mx-auto mt-8">
					<CardHeader className="text-center">
						<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
							<AlertTriangle className="h-6 w-6 text-red-600" />
						</div>
						<CardTitle className="text-xl">Component Error</CardTitle>
						<CardDescription>
							Something went wrong with this component. Please try refreshing.
						</CardDescription>
					</CardHeader>
					<CardContent>
						{process.env.NODE_ENV === "development" && this.state.error && (
							<div className="p-3 bg-red-50 border border-red-200 rounded-md mb-4">
								<p className="text-sm font-medium text-red-800 mb-1">
									Error Details:
								</p>
								<p className="text-xs text-red-700 font-mono break-all">
									{this.state.error.message}
								</p>
							</div>
						)}
						<Button className="w-full" onClick={reset}>
							<RefreshCw className="h-4 w-4 mr-2" />
							Try Again
						</Button>
					</CardContent>
				</Card>
			);
		}

		return this.props.children;
	}
}

// Hook version for functional components
export function useErrorBoundary() {
	const [error, setError] = useState<Error | null>(null);

	const resetError = useCallback(() => {
		setError(null);
	}, []);

	const captureError = useCallback((error: Error) => {
		setError(error);
	}, []);

	useEffect(() => {
		if (error) {
			throw error;
		}
	}, [error]);

	return { captureError, resetError };
}
