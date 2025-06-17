import { AuthContext, useAuth } from "@/elements/auth";
import { getFromCookie } from "@/services/cookieutils";
import { createContext, useContext, useState } from 'react';
export function WelcomePage() {
  console.log("loading welcome");
  const { user, loading} = useContext(AuthContext);
  console.log("Loaded the context in welcome page")
  console.log(user);
  
  const [welcomeloaded, setwelcomeloaded] = useState(false)


  const userData = ["asfdsafsa", "asfsad"]  //await fetchUser(uuid!);
  
  // store in cookie
  let v = getFromCookie('selectedgithubuser'); // TODO : put all cookie keys into cookie util script
  
  if (v == undefined){
    console.log("no github user selected yet");
    
  } else {
    console.log("");
  }
  

  return (
    <div>
      <h1>Welcome back to the repository {user?.reponame}!</h1>
      <p>Your role: {user?.role}</p>



      <p>Have you already selected which things you would like to select for summary?</p>
    </div>
  );
}