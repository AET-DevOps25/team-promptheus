import { useAuth } from "@/contextproviders/authprovider";
import React from "react";

export function QnAPage() {
	const { user, loading } = useAuth();
	return (
		<div>
			<h1>Asking and answering questions</h1>
		</div>
	);
}
