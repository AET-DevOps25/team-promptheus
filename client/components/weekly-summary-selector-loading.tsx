// biome-ignore-all lint/suspicious/noArrayIndexKey: skeletons are static
import { Calendar } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function WeeklySummaryLoading() {
	return (
		<Card>
			<CardHeader>
				<div className="flex items-center gap-2">
					<Calendar className="h-5 w-5" />
					<Skeleton className="h-6 w-48" />
				</div>
				<Skeleton className="h-4 w-80" />
			</CardHeader>
			<CardContent>
				<div className="space-y-4">
					{/* Summary Stats Loading */}
					<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
						{Array.from({ length: 4 }).map((_, i) => (
							<div className="text-center p-3 bg-slate-50 rounded-lg" key={i}>
								<Skeleton className="h-8 w-12 mx-auto mb-2" />
								<Skeleton className="h-3 w-16 mx-auto" />
							</div>
						))}
					</div>

					{/* Filters Loading */}
					<div className="flex flex-wrap gap-2 items-center justify-between">
						<div className="flex gap-2">
							<Skeleton className="h-10 w-64" />
							<Skeleton className="h-10 w-32" />
						</div>
						<div className="flex gap-2">
							<Skeleton className="h-8 w-24" />
							<Skeleton className="h-8 w-20" />
						</div>
					</div>

					{/* Items List Loading */}
					<div className="space-y-2">
						{Array.from({ length: 6 }).map((_, i) => (
							<div className="p-3 border rounded-lg bg-white" key={i}>
								<div className="flex items-start gap-3">
									<Skeleton className="h-4 w-4 mt-1" />
									<div className="flex-1 min-w-0">
										<div className="flex items-center gap-2 mb-1">
											<Skeleton className="h-5 w-16" />
											<Skeleton className="h-5 w-20" />
											<Skeleton className="h-5 w-24" />
										</div>
										<Skeleton className="h-4 w-3/4 mb-1" />
										<Skeleton className="h-3 w-full mb-2" />
										<div className="flex items-center gap-4">
											<Skeleton className="h-3 w-16" />
											<Skeleton className="h-3 w-20" />
										</div>
									</div>
								</div>
							</div>
						))}
					</div>

					{/* Action Buttons Loading */}
					<div className="flex gap-2 justify-end pt-4 border-t">
						<Skeleton className="h-9 w-32" />
						<Skeleton className="h-9 w-36" />
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
