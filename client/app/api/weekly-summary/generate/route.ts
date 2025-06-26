import { type NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
	try {
		const { items, userId } = await request.json();

		if (!items || !Array.isArray(items)) {
			return NextResponse.json(
				{ error: "Items array is required" },
				{ status: 400 },
			);
		}

		// Simulate AI processing delay
		await new Promise((resolve) => setTimeout(resolve, 2000));

		// Generate a mock summary based on selected items
		const doneItems = items.filter((item: any) => item.status === "done");
		const inProgressItems = items.filter(
			(item: any) => item.status === "in-progress",
		);
		const blockedItems = items.filter((item: any) => item.status === "blocked");

		const summary = `# Weekly Summary - ${new Date().toLocaleDateString()}

## 🎯 Completed This Week (${doneItems.length} items)

${doneItems
	.map(
		(item: any) => `### ${item.title}
- **Repository:** ${item.repository}
- **Author:** ${item.author}
- **Type:** ${item.type.toUpperCase()}
- **Description:** ${item.description}
- **Link:** ${item.url}

`,
	)
	.join("")}

## 🚧 In Progress (${inProgressItems.length} items)

${inProgressItems
	.map(
		(item: any) => `### ${item.title}
- **Repository:** ${item.repository}
- **Author:** ${item.author}
- **Type:** ${item.type.toUpperCase()}
- **Description:** ${item.description}
- **Status:** Currently in development
- **Link:** ${item.url}

`,
	)
	.join("")}

## 🚫 Blocked Items (${blockedItems.length} items)

${blockedItems
	.map(
		(item: any) => `### ${item.title}
- **Repository:** ${item.repository}
- **Author:** ${item.author}
- **Type:** ${item.type.toUpperCase()}
- **Description:** ${item.description}
- **Blocker:** Waiting for external dependencies
- **Link:** ${item.url}

`,
	)
	.join("")}

## 📊 Summary Statistics

- **Total Items:** ${items.length}
- **Completion Rate:** ${Math.round((doneItems.length / items.length) * 100)}%
- **Active Repositories:** ${[...new Set(items.map((item: any) => item.repository))].length}
- **Team Members Involved:** ${[...new Set(items.map((item: any) => item.author))].length}

## 🎯 Next Week's Focus

Based on current progress and blockers, the team should focus on:
1. Resolving blocked items to unblock progress
2. Completing in-progress work items
3. Addressing any technical debt identified this week

---
*Generated automatically by Prompteus AI on ${new Date().toLocaleString()}*`;

		return NextResponse.json({
			generatedAt: new Date().toISOString(),
			itemCount: items.length,
			summary,
		});
	} catch (error) {
		console.error("Summary generation error:", error);
		return NextResponse.json(
			{ error: "Internal server error" },
			{ status: 500 },
		);
	}
}
