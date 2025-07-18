"use client";

import { ArrowLeft, Github, KeyRound, Loader2, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
	const [userCode, setUserCode] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const router = useRouter();
	const userCodeId = useId();

	const handleLogin = async () => {
		if (!userCode.trim()) return;

		setIsLoading(true);
		try {
			// Store the usercode and redirect to dashboard
			localStorage.setItem("usercode", userCode.trim());
			router.push("/dashboard");
		} catch (error) {
			console.error("Login error:", error);
		} finally {
			setIsLoading(false);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === "Enter" && userCode.trim()) {
			handleLogin();
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
			<header className="border-b bg-white/80 backdrop-blur-sm">
				<div className="container mx-auto px-4 py-4">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-4">
							<Button asChild size="sm" variant="ghost">
								<Link href="/">
									<ArrowLeft className="h-4 w-4 mr-2" />
									Back to Home
								</Link>
							</Button>
						</div>
					</div>
				</div>
			</header>

			<main className="container mx-auto px-4 py-16 flex items-center justify-center min-h-[60vh]">
				<Card className="w-full max-w-md">
					<CardHeader className="text-center">
						<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
							<User className="h-6 w-6 text-blue-600" />
						</div>
						<CardTitle className="text-2xl">Access Your Dashboard</CardTitle>
						<CardDescription>
							Enter your user code or repository ID to continue to your
							personalized dashboard.
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-6">
						<div className="space-y-4">
							<div className="space-y-2">
								<Label htmlFor={userCodeId}>User Code / Repository ID</Label>
								<Input
									className="text-center"
									disabled={isLoading}
									id={userCodeId}
									onKeyDown={handleKeyPress}
									onChange={(e) => setUserCode(e.target.value)}
									placeholder="Enter your user code..."
									value={userCode}
								/>
							</div>
							<Button
								className="w-full"
								disabled={!userCode.trim()}
								onClick={handleLogin}
							>
								{isLoading ? (
									<>
										<Loader2 className="h-4 w-4 mr-2 animate-spin" />
										Accessing Dashboard...
									</>
								) : (
									<>
										<KeyRound className="h-4 w-4 mr-2" />
										Continue to Dashboard
									</>
								)}
							</Button>
						</div>

						<div className="relative">
							<div className="absolute inset-0 flex items-center">
								<span className="w-full border-t" />
							</div>
							<div className="relative flex justify-center text-xs uppercase">
								<span className="bg-white px-2 text-muted-foreground">Or</span>
							</div>
						</div>

						<div className="space-y-3">
							<Button asChild className="w-full" variant="outline">
								<Link href="/">
									<Github className="h-4 w-4 mr-2" />
									Set Up New Repository
								</Link>
							</Button>
						</div>

						<div className="text-center">
							<p className="text-xs text-muted-foreground">
								Don't have a user code?{" "}
								<Link className="text-blue-600 hover:underline" href="/">
									Get started here
								</Link>
							</p>
						</div>
					</CardContent>
				</Card>
			</main>
		</div>
	);
}
