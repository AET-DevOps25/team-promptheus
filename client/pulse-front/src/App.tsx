
import './App.css'
import React, { useContext } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Outlet } from "react-router";
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import LandingPage from './pages/landing'
import { AuthContext, AuthProvider, useAuth } from './contextproviders/authprovider';
import { UUIDForwarder } from './components/ui/UUIDForwarder';
import { Header } from './elements/header';
import { About } from './pages/About';
import SignupMain from './pages/signup';
import { WelcomePage } from './pages/WelcomePage';
import { SummaryViewing } from './pages/SummaryViewing';
import { Search } from 'lucide-react';
import { QnAPage } from './pages/QnAPage';
import GitHubContributions from './pages/github-contributions';
import { NoPage } from './pages/nopage';
import { SearchPage } from './pages/SearchPage';
import { GithubUserProvider } from './contextproviders/siteprovider';
import { SelectUserPage } from './pages/selectuser';


//{<div>Welcome! You are a viewing as a {user.role === 'dev' ? 'developer' : 'manager'} the repository {user.reponame}.</div>} />

function ProtectedLayout() {
  //const { user, loading } = useAuth();
  const { user, loading} = useContext(AuthContext);
  console.log("We load useAuth and got:")
  console.log(user)
  if (loading == false) {
      if (user == null) {
        return (<Navigate to="/landing" replace />);
      }
      else {
        console.log("Context detected. Loading a different layout!")
        return  ( <> <Header />  </>);
      }
    } 
    if (loading == true) {
      console.log("Loading...")
      return (<> <div> loading...</div></>)
    } else {
      console.log("impossible?")
    } 
}






{/*  -------- App Logic Providing Tree ----------- */}
function App() {

  return (

    //<AuthProvider>
    //  <RouterProvider router={router} />
    //</AuthProvider>
 
    <AuthProvider>
    <BrowserRouter> 
      <Routes>
          <Route path="/landing" element={<LandingPage />} /> 
          <Route path="/signup" element={<SignupMain />} />



          <GithubUserProvider> { /* keeps track which gh user is selected */}

            <Route element={<ProtectedLayout />}>
              <Route path="/" element={<WelcomePage />} />
              <Route path="/selectcontent" element={<GitHubContributions /> } />
              <Route path="/qna" element={<QnAPage /> } />
              <Route path="/summaryviewing" element={ <SummaryViewing/> } />
              <Route path="/search" element={ <SearchPage /> } />
              <Route path="/selectuser" element={<SelectUserPage />} />
            </Route>

          </GithubUserProvider>

          <Route 
            path="/:uuid" 
            element={<UUIDForwarder />} 
          />


          <Route path="about" element={ <About /> } />
          
          <Route path="*" element = { <NoPage /> } />
      </Routes>
    </BrowserRouter>   
    
    </AuthProvider>

   
  );
}


export default App