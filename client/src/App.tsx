import "./App.css";
import { useContext } from "react";
import { BrowserRouter, Route, Routes } from "react-router";
import { Navigate } from "react-router-dom";
import { UUIDForwarder } from "./components/ui/UUIDForwarder";
import { AuthContext, AuthProvider } from "./contextproviders/authprovider";
import { GithubUserProvider } from "./contextproviders/siteprovider";
import { Header } from "./elements/header";
import { About } from "./pages/About";
import GitHubContributions from "./pages/github-contributions";
import LandingPage from "./pages/landing";
import { NoPage } from "./pages/nopage";
import { QnAPage } from "./pages/QnAPage";
import { SearchPage } from "./pages/SearchPage";
import { SummaryViewing } from "./pages/SummaryViewing";
import { SelectUserPage } from "./pages/selectuser";
import SignupMain from "./pages/signup";
import { WelcomePage } from "./pages/WelcomePage";

//{<div>Welcome! You are a viewing as a {user.role === 'dev' ? 'developer' : 'manager'} the repository {user.reponame}.</div>} />

function ProtectedLayout() {
	//const { user, loading } = useAuth();
	const { user, loading } = useContext(AuthContext);
	console.log("We load useAuth and got:");
	console.log(user);
	if (loading == false) {
		if (user == null) {
			return <Navigate replace to="/landing" />;
		} else {
			console.log("Context detected. Loading a different layout!");
			return (
				<>
					{" "}
					<Header />{" "}
				</>
			);
		}
	}
	if (loading == true) {
		console.log("Loading...");
		return (
			<>
				{" "}
				<div> loading...</div>
			</>
		);
	} else {
		console.log("impossible?");
	}
}

{
	/*  -------- App Logic Providing Tree ----------- */
}
function App() {
	return (
		//<AuthProvider>
		//  <RouterProvider router={router} />
		//</AuthProvider>

		<AuthProvider>
			<BrowserRouter>
				<Routes>
					<Route element={<LandingPage />} path="/landing" />
					<Route element={<SignupMain />} path="/signup" />

					<GithubUserProvider>
						{" "}
						{/* keeps track which gh user is selected */}
						<Route element={<ProtectedLayout />}>
							<Route element={<WelcomePage />} path="/" />
							<Route element={<GitHubContributions />} path="/selectcontent" />
							<Route element={<QnAPage />} path="/qna" />
							<Route element={<SummaryViewing />} path="/summaryviewing" />
							<Route element={<SearchPage />} path="/search" />
							<Route element={<SelectUserPage />} path="/selectuser" />
						</Route>
					</GithubUserProvider>

					<Route element={<UUIDForwarder />} path="/:uuid" />

					<Route element={<About />} path="about" />

					<Route element={<NoPage />} path="*" />
				</Routes>
			</BrowserRouter>
		</AuthProvider>
	);
}

export default App;
