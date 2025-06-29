import { Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function Loading() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardContent className="flex flex-col items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-slate-600 mb-4" />
          <p className="text-slate-600 font-medium">Loading Prompteus...</p>
          <p className="text-sm text-muted-foreground mt-2">Preparing your GitHub insights</p>
        </CardContent>
      </Card>
    </div>
  );
}
