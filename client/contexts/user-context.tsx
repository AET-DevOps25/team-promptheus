"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface UserContextType {
	userId: string;
	setUserId: (id: string) => void;
	isLoading: boolean;
	isAuthenticated: boolean;
	clearUser: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

interface UserProviderProps {
	children: ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
	const [userId, setUserIdState] = useState<string>("");
	const [isLoading, setIsLoading] = useState(true);
	const [isAuthenticated, setIsAuthenticated] = useState(false);

	useEffect(() => {
		// Only run on client side
		if (typeof window !== "undefined") {
			const storedUserId = localStorage.getItem("usercode");
			if (storedUserId) {
				setUserIdState(storedUserId);
				setIsAuthenticated(true);
			} else {
				setIsAuthenticated(false);
			}
		}
		setIsLoading(false);
	}, []);

	const setUserId = (id: string) => {
		setUserIdState(id);
		setIsAuthenticated(!!id);
		if (typeof window !== "undefined") {
			localStorage.setItem("usercode", id);
		}
	};

	const clearUser = () => {
		setUserIdState("");
		setIsAuthenticated(false);
		if (typeof window !== "undefined") {
			localStorage.removeItem("usercode");
		}
	};

	const value: UserContextType = {
		userId,
		setUserId,
		isLoading,
		isAuthenticated,
		clearUser,
	};

	return (
		<UserContext.Provider value={value}>
			{children}
		</UserContext.Provider>
	);
}

export function useUser(): UserContextType {
	const context = useContext(UserContext);
	if (context === undefined) {
		throw new Error("useUser must be used within a UserProvider");
	}
	return context;
}
