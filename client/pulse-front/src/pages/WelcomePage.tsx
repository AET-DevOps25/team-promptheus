import { useAuth } from "@/elements/auth";

export function WelcomePage() {
  const { user , loading} = useAuth();
  return (
    <div>
      <h1>Welcome back to the repository {user?.reponame}!</h1>
      <p>Your role: {user?.role}</p>
      <p>Have you already selected which things you would like to select for summary?</p>
    </div>
  );
}