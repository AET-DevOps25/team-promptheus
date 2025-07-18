// biome-ignore-all lint/suspicious/noArrayIndexKey: skeletons are static
import { Calendar, FileText } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function WeeklySummaryLoading() {
	return (
		<>
			<header className="border-b bg-white">
				<div className="container mx-auto px-4 py-4">
					<div className="flex items-center gap-2">
						<Calendar className="h-6 w-6" />
						<Skeleton className="h-8 w-48" />
					</div>
					<Skeleton className="h-4 w-80" />
				</div>
			</header>

			<main className="container mx-auto px-4 py-8 max-w-6xl">
				<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
					{/* Main Content Loading */}
					<div className="lg:col-span-2 space-y-8">
						{/* Summary Builder Loading */}
						<Card>
							<CardHeader>
								<Skeleton className="h-6 w-48" />
								<Skeleton className="h-4 w-96" />
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									{/* Stats Grid Loading */}
									<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
										{Array.from({ length: 4 }).map((_, i) => (
											<div
												className="text-center p-3 bg-slate-50 rounded-lg"
												key={i}
											>
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

									{/* Items Loading */}
									<div className="space-y-2">
										{Array.from({ length: 8 }).map((_, i) => (
											<div className="p-3 border rounded-lg" key={i}>
												<div className="flex items-start gap-3">
													<Skeleton className="h-4 w-4 mt-1" />
													<div className="flex-1">
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

									{/* Actions Loading */}
									<div className="flex gap-2 justify-end pt-4 border-t">
										<Skeleton className="h-9 w-32" />
										<Skeleton className="h-9 w-36" />
									</div>
								</div>
							</CardContent>
						</Card>
					</div>

					{/* Sidebar Loading */}
					<div className="space-y-6">
						{/* Quick Actions Loading */}
						<Card>
							<CardHeader>
								<Skeleton className="h-5 w-24" />
							</CardHeader>
							<CardContent className="space-y-3">
								{Array.from({ length: 4 }).map((_, i) => (
									<Skeleton className="h-9 w-full" key={i} />
								))}
							</CardContent>
						</Card>

						{/* Templates Loading */}
						<Card>
							<CardHeader>
								<Skeleton className="h-5 w-32" />
								<Skeleton className="h-4 w-48" />
							</CardHeader>
							<CardContent>
								<div className="space-y-3">
									{Array.from({ length: 3 }).map((_, i) => (
										<div className="p-3 border rounded-lg" key={i}>
											<Skeleton className="h-4 w-3/4 mb-2" />
											<Skeleton className="h-3 w-full" />
										</div>
									))}
								</div>
							</CardContent>
						</Card>

						{/* Recent Summaries Loading */}
						<Card>
							<CardHeader>
								<div className="flex items-center gap-2">
									<FileText className="h-5 w-5" />
									<Skeleton className="h-5 w-32" />
								</div>
							</CardHeader>
							<CardContent>
								<div className="space-y-3">
									{Array.from({ length: 3 }).map((_, i) => (
										<div
											className="flex items-center gap-3 p-2 border rounded"
											key={i}
										>
											<Skeleton className="h-8 w-8" />
											<div className="flex-1">
												<Skeleton className="h-4 w-2/3 mb-1" />
												<Skeleton className="h-3 w-1/2" />
											</div>
										</div>
									))}
								</div>
							</CardContent>
						</Card>
					</div>
				</div>
			</main>
		</>
	);
}
