// biome-ignore-all lint/suspicious/noArrayIndexKey: skeletons are static
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function QALoading() {
  return (
    <>
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-80" />
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            {/* Ask Question Card Loading */}
            <Card className="mb-8">
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-96" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-24 w-full mb-4" />
                <div className="flex justify-between items-center">
                  <Skeleton className="h-3 w-64" />
                  <Skeleton className="h-9 w-24" />
                </div>
              </CardContent>
            </Card>

            {/* Filter Tabs Loading */}
            <div className="flex gap-2 mb-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton className="h-8 w-24" key={i} />
              ))}
            </div>

            {/* Q&A Items Loading */}
            <div className="space-y-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-3 mb-4">
                      <Skeleton className="h-8 w-8 rounded-full" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Skeleton className="h-4 w-20" />
                          <Skeleton className="h-4 w-24" />
                          <Skeleton className="h-5 w-16" />
                        </div>
                        <Skeleton className="h-4 w-3/4 mb-2" />
                        <div className="flex gap-2">
                          <Skeleton className="h-4 w-16" />
                          <Skeleton className="h-4 w-20" />
                        </div>
                      </div>
                    </div>
                    <div className="border-t my-4" />
                    <div className="flex items-start gap-3">
                      <Skeleton className="h-8 w-8 rounded-full" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-24 mb-2" />
                        <Skeleton className="h-16 w-full" />
                      </div>
                    </div>
                    <div className="flex justify-between mt-4 pt-4 border-t">
                      <div className="flex gap-4">
                        <Skeleton className="h-6 w-12" />
                        <Skeleton className="h-6 w-12" />
                      </div>
                      <Skeleton className="h-6 w-32" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Sidebar Loading */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-24" />
              </CardHeader>
              <CardContent className="space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div className="flex justify-between items-center" key={i}>
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-5 w-8" />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-40" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton className="h-12 w-full" key={i} />
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
