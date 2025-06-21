// this is the client side of the logic implementing the mapping between link <-> (repository, dev/manager)
// it sets a cookie

import { createContext, useContext, useEffect, useState } from "react";
import { getFromCookie } from "@/services/cookieutils";

type Userrole = {
	uuid: string;
	reponame: string;
	role: string;
} | null;

export const AuthContext = createContext<{
	user: Userrole;
	loading: boolean;
}>({
	loading: true,
	user: null,
}); //({ user: null, loading: true, api: null });

export function AuthProvider({ children }: { children: React.ReactNode }) {
	const [user, setUser] = useState<Userrole>(null);
	const [loading, setLoading] = useState(true); // when this is initialized, it should load
	//const navigate = useNavigate();

	// sets user: either from cookie or from server (which is then immediatedly stored to cookie)
	useEffect(() => {
		//const cookie = document.cookie.split('; ')
		//    .find(row => row.startsWith('user='));
		console.log("doing auth");
		const cookie = getFromCookie("user");
		if (cookie) {
			console.log("loaded cookie:");
			console.log(cookie);
			//setUser(JSON.parse(  //cookie.split('=')[1]));

			(async () => {
				// Do something before delay
				console.log("before delay");

				await new Promise((f) => setTimeout(f, 1000));

				// Do something after
				console.log("after delay");
			})();

			setUser({
				reponame: "reponames",
				role: "arole",
				uuid: "7f2c97bd-fc21-4eb0-a3d8-f4ac7986ee64",
			});
			setLoading(false);
		} else {
			console.log("no cookie found");
			setLoading(false);
		} //else {
		// no cookie and not uuid
		//navigate("/nopage");
		//}
	}, [setUser, setLoading]);

	return (
		<AuthContext.Provider value={{ loading, user }}>
			{children}
		</AuthContext.Provider>
	);
}

export const useAuth = () => useContext(AuthContext);
