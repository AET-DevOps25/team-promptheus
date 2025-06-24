import { Avatar } from "@radix-ui/react-avatar";
import { AlertCircle, Check, Github, Loader2, Users } from "lucide-react";
import { useContext, useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { AuthContext } from "@/contextproviders/authprovider";
import { GithubUserProviderContext } from "@/contextproviders/siteprovider";
import type { GitHubContributor } from "@/types/github";

export function SelectUserPage() {
	// initialise fast loading react states
	const [isLoading, setIsLoading] = useState(false);
	const [contributors, setContributors] = useState<GitHubContributor[]>([]);
	const [error, setError] = useState<string | null>(null);

	// load slower context
	const { user } = useContext(AuthContext);
	const { selectedUser, setSelectedUser } = useContext(
		GithubUserProviderContext,
	);

	useEffect(() => {
		setIsLoading(true);
		setError(null);

		fetchRepoContributors()
			.then((contributorsList) => setContributors(contributorsList))
			.catch((err) =>
				setError(
					err instanceof Error ? err.message : "Failed to fetch contributors",
				),
			)
			.finally(() => setIsLoading(false));
	}, []);
	async function fetchRepoContributors() {
		return [];
	}
	const handleSelectUser = (user: GitHubContributor) => {
		setSelectedUser(user);
		//localStorage.setItem("selectedGitHubUser", JSON.stringify(user))

		// Dispatch custom event to notify other components
		// not needed. TODO: remove window.dispatchEvent(new Event("selectedUserChanged"))
	};

	return (
		<Card className="w-full max-w-4xl mx-auto">
			<CardHeader>
				<div className="flex items-center justify-between">
					<div>
						<CardTitle className="flex items-center gap-2">
							<Users className="h-5 w-5" />
							Repository Contributors
						</CardTitle>
						<CardDescription>
							Select a user from the contributors of {user?.reponame}
						</CardDescription>
					</div>
					{selectedUser && (
						<div className="flex items-center gap-2">
							<Badge className="flex items-center gap-2" variant="secondary">
								<Check className="h-3 w-3" />
								Selected: {selectedUser.login}
							</Badge>
							<Button
								onClick={() => handleSelectUser(selectedUser)}
								size="sm"
								variant="outline"
							>
								Clear
							</Button>
						</div>
					)}
				</div>
			</CardHeader>
			<CardContent>
				{isLoading ? (
					<div className="flex justify-center items-center py-12">
						<Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
						<span className="ml-2 text-muted-foreground">
							Loading contributors...
						</span>
					</div>
				) : error ? (
					<Alert variant="destructive">
						<AlertCircle className="h-4 w-4" />
						<AlertTitle>Error</AlertTitle>
						<AlertDescription>{error}</AlertDescription>
					</Alert>
				) : contributors.length === 0 ? (
					<div className="text-center py-12 text-muted-foreground">
						No contributors found for this repository
					</div>
				) : (
					<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
						{contributors.map((contributor) => (
							<Card
								className={`cursor-pointer transition-all hover:shadow-md ${
									selectedUser?.id === contributor.id
										? "ring-2 ring-primary bg-primary/5"
										: "hover:bg-muted/50"
								}`}
								key={contributor.id}
								onClick={() => handleSelectUser(contributor)}
							>
								<CardContent className="p-4">
									<div className="flex items-center gap-3">
										<Avatar className="h-12 w-12">
											<AvatarImage
												alt={contributor.login}
												src={contributor.avatar_url || "/placeholder.svg"}
											/>
											<AvatarFallback>
												{contributor.login.substring(0, 2).toUpperCase()}
											</AvatarFallback>
										</Avatar>
										<div className="flex-1 min-w-0">
											<div className="flex items-center gap-2">
												<h3 className="font-medium truncate">
													{contributor.login}
												</h3>
												{selectedUser?.id === contributor.id && (
													<Check className="h-4 w-4 text-primary flex-shrink-0" />
												)}
											</div>
											<div className="flex items-center gap-1 text-sm text-muted-foreground">
												<Github className="h-3 w-3" />
												<span>{contributor.contributions} contributions</span>
											</div>
										</div>
									</div>
								</CardContent>
							</Card>
						))}
					</div>
				)}
			</CardContent>
		</Card>
	);
}
