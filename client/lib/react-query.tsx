"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function ReactQueryProvider({
	children,
}: {
	children: React.ReactNode;
}) {
	const [queryClient] = useState(
		() =>
			new QueryClient({
				defaultOptions: {
					mutations: {
						retry: (failureCount, error) => {
							// Don't retry mutations on client errors (4xx)
							if (error && typeof error === "object" && "status" in error) {
								const status = error.status as number;
								if (status >= 400 && status < 500) {
									return false;
								}
							}
							// Retry up to 2 times for server errors
							return failureCount < 2;
						},
					},
					queries: {
						retry: (failureCount, error) => {
							// Don't retry on 404s
							if (
								error &&
								typeof error === "object" &&
								"status" in error &&
								error.status === 404
							) {
								return false;
							}
							// Retry up to 3 times for other errors
							return failureCount < 3;
						}, // 1 minute
						// With SSR, we usually want to set some default staleTime
						// above 0 to avoid refetching immediately on the client
						staleTime: 60 * 1000,
					},
				},
			}),
	);

	return (
		<QueryClientProvider client={queryClient}>
			{children}
			<ReactQueryDevtools initialIsOpen={false} />
		</QueryClientProvider>
	);
}
