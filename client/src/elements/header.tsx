import { User } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getLocalStorageItem } from "@/services/localstorageservice";
import { useAuth } from "../contextproviders/authprovider";

const navItems = [
	{ href: "/", label: "Home" },
	{ href: "/about", label: "About" },
	{ href: "/qna", label: "Q/A" },
	{ href: "/search", label: "Search" },
	{ href: "/selectcontent", label: "Select content" },
];

export function Header() {
	const { user, loading } = useAuth();
	const location = useLocation();
	const [selectedUser, setSelectedUser] = useState<{
		login: string;
		avatar_url: string;
	} | null>(null);

	// update react state
	useEffect(() => {
		const saved = getLocalStorageItem("selectedGitHubUser"); // localStorage.getItem("selectedGitHubUser")
		if (saved) {
			setSelectedUser(saved);
		}
	}, []);

	return (
		<div>
			<header className="w-full max-w-4xl mx-auto mb-8">
				<div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b">
					<h1 className="text-3xl font-bold tracking-tight">
						<span className="font-medium">Auto</span>Pulse
					</h1>

					<div> Repository: {user?.reponame}</div>

					<div className="flex items-center gap-4">
						{/* pannel */}
						<nav className="flex flex-wrap gap-1">
							{navItems.map((item) => (
								<Link
									className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
										location.pathname === item.href
											? "bg-primary text-primary-foreground"
											: "text-muted-foreground hover:text-foreground hover:bg-muted"
									}`}
                                    key={item.href}
									to={item.href}
								>
									{item.label}
								</Link>
							))}
						</nav>

						{/* avatar */}

						<div className="flex items-center gap-2">
							<Avatar className="h-8 w-8">
								{selectedUser ? (
									<>
										<AvatarImage
											alt={selectedUser.login}
											src={selectedUser.avatar_url || "/placeholder.svg"}
										/>
										<AvatarFallback>
											{selectedUser.login.substring(0, 2).toUpperCase()}
										</AvatarFallback>
									</>
								) : (
									<AvatarFallback className="bg-muted">
										<User className="h-4 w-4 text-muted-foreground" />
									</AvatarFallback>
								)}
							</Avatar>
							{selectedUser && (
								<span className="text-sm font-medium text-muted-foreground">
									{selectedUser.login}
								</span>
							)}
						</div>
					</div>
				</div>
			</header>

			<Outlet />
		</div>
	);
}
