import { useAuth } from "@/contextproviders/authprovider";

export default function QnAPage() {
	const { user, loading } = useAuth();
	return (
		<div>
			<h1>Asking and answering questions</h1>
		</div>
	);
}
