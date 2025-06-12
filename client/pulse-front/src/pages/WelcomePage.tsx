import { AuthContext, useAuth } from "@/elements/auth";
import { createContext, useContext } from 'react';
export function WelcomePage() {
  console.log("loading welcome");
  const { user, loading} = useContext(AuthContext);
  console.log("Loaded the context in welcome page")
  console.log(user);
  return (
    <div>
      <h1>Welcome back to the repository {user?.reponame}!</h1>
      <p>Your role: {user?.role}</p>
      <p>Have you already selected which things you would like to select for summary?</p>
    </div>
  );
}