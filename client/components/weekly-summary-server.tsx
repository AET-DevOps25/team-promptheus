import { Suspense } from "react";
import { WeeklySummarySelector } from "./weekly-summary-selector";
import { WeeklySummaryLoading } from "./weekly-summary-selector-loading";

interface WeeklySummaryServerProps {
	userId: string;
}

async function WeeklySummaryData({ userId }: WeeklySummaryServerProps) {
	// Simulate server-side data fetching delay
	await new Promise((resolve) => setTimeout(resolve, 1000));

	return <WeeklySummarySelector userId={userId} />;
}

export function WeeklySummaryServer({ userId }: WeeklySummaryServerProps) {
	return (
		<Suspense fallback={<WeeklySummaryLoading />}>
			<WeeklySummaryData userId={userId} />
		</Suspense>
	);
}
