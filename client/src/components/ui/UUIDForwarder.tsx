import { useEffect } from "react";
import { Navigate } from "react-router-dom";
import { updateCookie } from "@/services/cookieutils";

export function UUIDForwarder() {
	//const { uuid } = useParams();

	// const urlParams = new URLSearchParams(window.location.search);
	// const _uuid = urlParams.get("uuid");

	useEffect(() => {
		async function handleUUID() {
			try {
				// obtain uuid
				console.log("obtain uuid");

				// ask spring for uuid mapping
				const userData = ["thisisareponame", "thisisarole"]; //await fetchUser(uuid!);

				// store in cookie
				updateCookie("user", userData);

				//document.cookie = `user=${JSON.stringify(userData)}; path=/; max-age=${30 * 24 * 60 * 60}`;
			} catch (error) {
				console.error("Failed to fetch user", error);
			}
		}

		handleUUID();
	}, []);

	return <Navigate replace to="/" />;
}
