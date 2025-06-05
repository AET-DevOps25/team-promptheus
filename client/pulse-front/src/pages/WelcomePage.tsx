import { useAuth } from "@/elements/auth";

export function WelcomePage() {
  const { user } = useAuth();
  return (
    <div>
      <h1>Welcome back, {user?.name}!</h1>
      <p>Your role: {user?.role}</p>
    </div>
  );
}