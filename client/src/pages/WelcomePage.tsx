import { Button } from "@/components/ui/button";
import { AuthContext } from "@/contextproviders/authprovider";
import { GithubUserProviderContext } from "@/contextproviders/siteprovider";
import { getFromCookie } from "@/services/cookieutils";
import { useContext, useState } from "react";
import { Navigate } from "react-router-dom";

export function WelcomePage() {
	console.log("loading consumers");
	// loading context consumers
	const { user, loading } = useContext(AuthContext);
	const { selectedUser, setSelectedUser } = useContext(
		GithubUserProviderContext,
	);

	console.log("Loaded the context in welcome page");
	console.log(user);

	const [welcomeloaded, setwelcomeloaded] = useState(false);

	const userData = ["asfdsafsa", "asfsad"]; //await fetchUser(uuid!);

	// store in cookie
	let v = getFromCookie("selectedgithubuser"); // TODO : put all cookie keys into cookie util script

	if (v == undefined) {
		console.log("no github user selected yet");
	} else {
		console.log("");
	}

	const handleSelectUserButtonClick = () => {
		<Navigate to="/landing" replace />;
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
					<Button variant="outline" onClick={handleSelectUserButtonClick}>
						Select github user contributor
					</Button>
				</div>
			)}
		</div>
	);
}
