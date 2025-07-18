// biome-ignore-all lint/suspicious/noArrayIndexKey: skeletons are static
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLoading() {
	return (
		<>
			<header className="border-b bg-white">
				<div className="container mx-auto px-4 py-4">
					<Skeleton className="h-8 w-64 mb-2" />
					<Skeleton className="h-4 w-96" />
				</div>
			</header>

			<main className="container mx-auto px-4 py-8">
				{/* Stats Cards Loading */}
				<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
					{Array.from({ length: 4 }).map((_, i) => (
						<Card key={i}>
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<Skeleton className="h-4 w-24" />
								<Skeleton className="h-4 w-4" />
							</CardHeader>
							<CardContent>
								<Skeleton className="h-8 w-12 mb-2" />
								<Skeleton className="h-3 w-20" />
							</CardContent>
						</Card>
					))}
				</div>

				{/* Search Card Loading */}
				<Card className="mb-8">
					<CardHeader>
						<Skeleton className="h-6 w-32" />
						<Skeleton className="h-4 w-80" />
					</CardHeader>
					<CardContent>
						<Skeleton className="h-10 w-full" />
					</CardContent>
				</Card>

				{/* Q&A Card Loading */}
				<Card className="mb-8">
					<CardHeader>
						<Skeleton className="h-6 w-24" />
						<Skeleton className="h-4 w-64" />
					</CardHeader>
					<CardContent>
						<div className="space-y-3">
							<div className="p-3 bg-slate-50 rounded-lg">
								<Skeleton className="h-4 w-3/4 mb-2" />
								<Skeleton className="h-3 w-full mb-2" />
								<div className="flex gap-2">
									<Skeleton className="h-5 w-16" />
									<Skeleton className="h-5 w-20" />
								</div>
							</div>
							<div className="flex gap-2">
								<Skeleton className="h-8 flex-1" />
								<Skeleton className="h-8 flex-1" />
							</div>
						</div>
					</CardContent>
				</Card>

				{/* Activity Card Loading */}
				<Card>
					<CardHeader>
						<Skeleton className="h-6 w-32" />
						<Skeleton className="h-4 w-64" />
					</CardHeader>
					<CardContent>
						<div className="space-y-4">
							{Array.from({ length: 3 }).map((_, i) => (
								<div className="flex items-start gap-3" key={i}>
									<Skeleton className="h-5 w-16" />
									<div className="flex-1">
										<Skeleton className="h-4 w-3/4 mb-1" />
										<Skeleton className="h-3 w-1/2" />
									</div>
								</div>
							))}
						</div>
					</CardContent>
				</Card>
			</main>
		</>
	);
}
