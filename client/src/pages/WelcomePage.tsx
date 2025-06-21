import { useContext, useState } from "react";
import { Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { AuthContext } from "@/contextproviders/authprovider";
import { GithubUserProviderContext } from "@/contextproviders/siteprovider";
import { getFromCookie } from "@/services/cookieutils";

export function WelcomePage() {
	console.log("loading consumers");
	// loading context consumers
	const { user, loading } = useContext(AuthContext);
	const { selectedUser, setSelectedUser } = useContext(
		GithubUserProviderContext,
	);

	console.log("Loaded the context in welcome page");
	console.log(user);

	// store in cookie
	const v = getFromCookie("selectedgithubuser"); // TODO : put all cookie keys into cookie util script

	if (v === undefined) {
		console.log("no github user selected yet");
	} else {
		console.log("");
	}

	const handleSelectUserButtonClick = () => {
		<Navigate replace to="/landing" />;
	};

	return (
		<div>
			<h1>Welcome back to the repository {user?.reponame}!</h1>
			<p>Your role: {user?.role}</p>

			{selectedUser ? (
				<div>
					<p>
						Have you already selected which things you would like to select for
						summary?
					</p>
					<p> :D </p>
				</div>
			) : (
				<div>
					<p>
						You have not selected for which contributor you would like to use
						this service for. Please select a user:
					</p>
					<Button onClick={handleSelectUserButtonClick} variant="outline">
						Select github user contributor
					</Button>
				</div>
			)}
		</div>
	);
}
