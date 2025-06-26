import { type NextRequest, NextResponse } from "next/server";

export async function PATCH(
	request: NextRequest,
	{ params }: { params: { id: string } },
) {
	try {
		const { status } = await request.json();
		const { id } = params;

		if (!["approved", "rejected"].includes(status)) {
			return NextResponse.json({ error: "Invalid status" }, { status: 400 });
		}

		// Simulate API delay
		await new Promise((resolve) => setTimeout(resolve, 500));

		// In a real app, you'd update the database here
		return NextResponse.json({
			id,
			message: `Q&A item ${status} successfully`,
			status,
		});
	} catch (error) {
		console.error("Q&A update error:", error);
		return NextResponse.json(
			{ error: "Internal server error" },
			{ status: 500 },
		);
	}
}
