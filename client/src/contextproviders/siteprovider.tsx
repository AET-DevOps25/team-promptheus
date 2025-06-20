import type { GitHubContributor } from "@/services/api";
import { createContext, useEffect, useState } from "react";





export const GithubUserProviderContext = createContext<{
  selectedUser: GitHubContributor | null;
  setSelectedUser: (user: GitHubContributor | null) => void;
}>({
  selectedUser: null,
  setSelectedUser: () => {},
});



export function GithubUserProvider({ children }: { children: React.ReactNode }) {
  
    // generate react update functions and initialize with value if already present in localStorage
    const [selectedUser, setSelectedUser] = useState<GitHubContributor | null>(() => {
        const saved = localStorage.getItem("selectedGitHubUser");
        return saved ? JSON.parse(saved) : null;
    });

    // syncing with localStorage
    useEffect(() => {
    if (selectedUser) {
        localStorage.setItem("selectedGitHubUser", JSON.stringify(selectedUser));
    } else {
        localStorage.removeItem("selectedGitHubUser");
    }
    }, [selectedUser]); // <-- hook on selectedUser

    // returning context provider
    return (
    <GithubUserProviderContext.Provider value={{ selectedUser, setSelectedUser }}>
      {children}
    </GithubUserProviderContext.Provider>
  );




}