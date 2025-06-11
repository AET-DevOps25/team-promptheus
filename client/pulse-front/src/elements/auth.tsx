

// this is the client side of the logic implementing the mapping between link <-> (repository, dev/manager)
// it sets a cookie


import { getCookie, getFromCookie } from '@/services/cookieutils';
import { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";

type Userrole = {
    uuid: string;
    reponame: string;
    role: string;
  } | null;

export const AuthContext = createContext<{
    user: Userrole;
    loading: boolean;
}>({
    user: null,
    loading: true
}) ; //({ user: null, loading: true, api: null });


export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<Userrole>(null);
    const [loading, setLoading] = useState(true);  // when this is initialized, it should load
    //const navigate = useNavigate();
    

    // sets user: either from cookie or from server (which is then immediatedly stored to cookie)
    useEffect(() => {

            
           
            //const cookie = document.cookie.split('; ')
            //    .find(row => row.startsWith('user='));
        console.log("doing auth")
        const cookie = getFromCookie('user');
        if (cookie) {
            console.log("loaded cookie:")
            console.log(cookie);
            //setUser(JSON.parse(  //cookie.split('=')[1]));
            
            setUser(  {
                    uuid: "7f2c97bd-fc21-4eb0-a3d8-f4ac7986ee64",
                    reponame: "reponames",
                    role: "arole"
                 } )
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
        <AuthContext.Provider value={{user, loading}}>
            {children}
        </AuthContext.Provider>
    )
}

/* 
function getCookie(name: string) {
  // Simple cookie parser
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift();
} */

export const useAuth = () => useContext(AuthContext);