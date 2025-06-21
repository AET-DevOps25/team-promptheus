import React from "react";
import { useAuth } from "@/contextproviders/authprovider";

export function SummaryViewing() {
	const { user } = useAuth();
	return (
		<div>
			<h1>Summary viewing</h1>
		</div>
	);
}
