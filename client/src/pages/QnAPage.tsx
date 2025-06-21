import React from "react";
import { useAuth } from "@/contextproviders/authprovider";

export function QnAPage() {
	const { user, loading } = useAuth();
	return (
		<div>
			<h1>Asking and answering questions</h1>
		</div>
	);
}
