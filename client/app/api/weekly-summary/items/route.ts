import { NextResponse } from "next/server";

// Mock data for development
const mockSummaryItems = [
	{
		author: "jane.smith",
		date: "2024-01-14T15:45:00Z",
		description:
			"Added connection pooling to reduce database connection overhead. Includes configuration options and monitoring metrics.",
		id: "1",
		repository: "api-backend",
		selected: false,
		status: "done",
		title: "Implement database connection pooling for better performance",
		type: "pr",
		url: "https://github.com/org/api-backend/pull/456",
	},
	{
		author: "john.doe",
		date: "2024-01-15T10:30:00Z",
		description:
			"Resolved issue where users couldn't log in after password reset. Updated JWT token validation and added proper error handling.",
		id: "2",
		repository: "auth-service",
		selected: false,
		status: "done",
		title: "Fix authentication bug in user login flow",
		type: "commit",
		url: "https://github.com/org/auth-service/commit/abc123",
	},
	{
		author: "mike.wilson",
		date: "2024-01-13T09:20:00Z",
		description:
			"Background jobs are not properly cleaning up resources, causing memory usage to grow over time.",
		id: "3",
		repository: "job-processor",
		selected: false,
		status: "in-progress",
		title: "Memory leak in background job processor",
		type: "issue",
		url: "https://github.com/org/job-processor/issues/789",
	},
	{
		author: "sarah.johnson",
		date: "2024-01-12T14:10:00Z",
		description:
			"Implementing sliding window rate limiting to improve API performance and prevent abuse.",
		id: "4",
		repository: "api-gateway",
		selected: false,
		status: "in-progress",
		title: "Add API rate limiting implementation",
		type: "pr",
		url: "https://github.com/org/api-gateway/pull/321",
	},
	{
		author: "alex.brown",
		date: "2024-01-11T11:00:00Z",
		description:
			"Waiting for infrastructure team approval before proceeding with the database schema changes.",
		id: "5",
		repository: "api-backend",
		selected: false,
		status: "blocked",
		title: "Database migration pending approval",
		type: "issue",
		url: "https://github.com/org/api-backend/issues/654",
	},
	{
		author: "john.doe",
		date: "2024-01-15T14:30:00Z",
		description:
			"AI analysis identified database query optimization and memory management issues as primary bottlenecks.",
		id: "6",
		repository: "api-backend",
		selected: false,
		status: "done",
		title: "What are the main performance bottlenecks in our API?",
		type: "qa",
		url: "/qa#1",
	},
];

export async function GET() {
	// Simulate API delay
	await new Promise((resolve) => setTimeout(resolve, 1000));

	return NextResponse.json({
		items: mockSummaryItems,
		total: mockSummaryItems.length,
	});
}
