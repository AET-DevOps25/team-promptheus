

// this is the client side of the logic implementing the mapping between link <-> (repository, dev/manager)
// it sets a cookie


import { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";

type Userrole = {
    uuid: string;
    reponame: string;
    role: string;
  } | null;
  
const AuthContext = createContext<{
    user: Userrole;
    loading: boolean;
}>({ user: null, loading: true });


export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<Userrole>(null);
    const [loading, setLoading] = useState(true);  // when this is initialized, it should load

    const navigate = useNavigate();
    
    useEffect(() => {

        async function anon_fetch() {
            
            const urlParams = new URLSearchParams(window.location.search);
            const uuid = urlParams.get('uuid');

            if (uuid) {
                // 2. If UUID exists, fetch user data
                const response = await fetch(`/api/user/${uuid}`);
                const userData = await response.json();
                
                // 3. Set cookie (optional) and context
                document.cookie = `user=${JSON.stringify(userData)}; path=/; max-age=86400`;
                setUser(userData);
              } else {
                // 4. Check for existing cookie
                const cookie = document.cookie.split('; ')
                  .find(row => row.startsWith('user='));
                if (cookie) {
                    setUser(JSON.parse(cookie.split('=')[1]));
                } else {
                    // no cookie and not uuid
                    navigate("/nopage");
                }
              }
            
              setLoading(false);
        }

        anon_fetch();
    }, []);

    return (
        <AuthContext.Provider value={{user, loading}}>
            {children}
        </AuthContext.Provider>
    )
}


export const useAuth = () => useContext(AuthContext);