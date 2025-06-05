import { useAuth } from "@/elements/auth";
import { useEffect } from "react";
import { Navigate, useParams } from "react-router-dom";

export function UUIDForwarder() {
  const { user, loading, api } = useAuth();
  //const { uuid } = useParams();
  
    
    const urlParams = new URLSearchParams(window.location.search);
    const uuid = urlParams.get('uuid');


  useEffect(() => {
    async function handleUUID() {
      try {

        // obtain uuid


        // ask spring for uuid mapping
        const userData = await api.fetchUser(uuid!);

        // store in cookie
        document.cookie = `user=${JSON.stringify(userData)}; path=/; max-age=${30 * 24 * 60 * 60}`;

      } catch (error) {
        console.error('Failed to fetch user', error);
      }
    }

    handleUUID();
  }, [uuid, api]);

  return <Navigate to="/" replace />;
}