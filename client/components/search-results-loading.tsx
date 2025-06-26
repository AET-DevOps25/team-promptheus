import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function SearchResultsLoading() {
	return (
		<div className="space-y-3">
			<div className="flex items-center justify-between">
				<Skeleton className="h-4 w-48" />
			</div>
			{Array.from({ length: 5 }).map((_, i) => (
				<Card className="hover:shadow-md transition-shadow" key={i}>
					<CardContent className="p-4">
						<div className="flex items-start justify-between gap-4">
							<div className="flex-1 min-w-0">
								<div className="flex items-center gap-2 mb-2">
									<Skeleton className="h-5 w-16" />
									<Skeleton className="h-5 w-20" />
									<Skeleton className="h-4 w-12" />
								</div>
								<Skeleton className="h-4 w-3/4 mb-1" />
								<Skeleton className="h-3 w-full mb-2" />
								<div className="flex items-center gap-4">
									<Skeleton className="h-3 w-16" />
									<Skeleton className="h-3 w-20" />
								</div>
							</div>
							<Skeleton className="h-8 w-8" />
						</div>
					</CardContent>
				</Card>
			))}
		</div>
	);
}
