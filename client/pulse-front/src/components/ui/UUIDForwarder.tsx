import { useAuth } from "@/elements/auth";
import { fetchUser } from "@/services/api";
import { updateCookie } from "@/services/cookieutils";
import { useEffect } from "react";
import { Navigate, useParams } from "react-router-dom";

export function UUIDForwarder() {

  //const { uuid } = useParams();
  
    
  const urlParams = new URLSearchParams(window.location.search);
  const uuid = urlParams.get('uuid');


  useEffect(() => {
    async function handleUUID() {
      try {

        // obtain uuid
        console.log("obtain uuid")

        // ask spring for uuid mapping
        const userData = ["thisisareponame", "thisisarole"]  //await fetchUser(uuid!);
        
        // store in cookie
        updateCookie('user', userData)
        
        //document.cookie = `user=${JSON.stringify(userData)}; path=/; max-age=${30 * 24 * 60 * 60}`;

      } catch (error) {
        console.error('Failed to fetch user', error);
      }
    }

    handleUUID();
  }, [uuid]);

  return <Navigate to="/" replace />;
}