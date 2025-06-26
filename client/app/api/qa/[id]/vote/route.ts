import { type NextRequest, NextResponse } from "next/server";

export async function POST(
	request: NextRequest,
	{ params }: { params: { id: string } },
) {
	try {
		const { type } = await request.json();
		const { id } = params;

		if (!["up", "down"].includes(type)) {
			return NextResponse.json({ error: "Invalid vote type" }, { status: 400 });
		}

		// Simulate API delay
		await new Promise((resolve) => setTimeout(resolve, 300));

		// Mock updated item with new vote counts
		const updatedItem = {
			downvotes:
				type === "down"
					? Math.floor(Math.random() * 5) + 1
					: Math.floor(Math.random() * 3),
			id,
			upvotes:
				type === "up"
					? Math.floor(Math.random() * 20) + 1
					: Math.floor(Math.random() * 15),
		};

		return NextResponse.json(updatedItem);
	} catch (error) {
		console.error("Vote error:", error);
		return NextResponse.json(
			{ error: "Internal server error" },
			{ status: 500 },
		);
	}
}
