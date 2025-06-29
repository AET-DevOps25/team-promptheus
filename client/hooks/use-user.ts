"use client";

import { useState, useEffect } from "react";

interface UseUserResult {
	userId: string;
	setUserId: (id: string) => void;
	isLoading: boolean;
	isAuthenticated: boolean;
	clearUser: () => void;
}

/**
 * Custom hook to manage user ID across the application
 * Currently reads from localStorage with fallback to "abc"
 * TODO: Replace with proper authentication system
 */
export function useUser(): UseUserResult {
	const [userId, setUserIdState] = useState<string>("abc");
	const [isLoading, setIsLoading] = useState(true);
	const [isAuthenticated, setIsAuthenticated] = useState(false);

	useEffect(() => {
		// Only run on client side
		if (typeof window !== "undefined") {
			const storedUserId = localStorage.getItem("usercode");
			if (storedUserId && storedUserId !== "abc") {
				setUserIdState(storedUserId);
				setIsAuthenticated(true);
			} else {
				// Keep default "abc" but mark as not authenticated
				setIsAuthenticated(false);
			}
		}
		setIsLoading(false);
	}, []);

	const setUserId = (id: string) => {
		setUserIdState(id);
		setIsAuthenticated(id !== "abc");
		if (typeof window !== "undefined") {
			localStorage.setItem("usercode", id);
		}
	};

	const clearUser = () => {
		setUserIdState("abc");
		setIsAuthenticated(false);
		if (typeof window !== "undefined") {
			localStorage.removeItem("usercode");
		}
	};

	return {
		userId,
		setUserId,
		isLoading,
		isAuthenticated,
		clearUser,
	};
}
