
import './App.css'
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router";
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import LandingPage from './pages/landing'
import { AuthProvider, useAuth } from './elements/auth';
import { UUIDForwarder } from './components/ui/UUIDForwarder';
import { Header } from './elements/header';
import { About } from './pages/About';
import SignupMain from './pages/signup';
import { WelcomePage } from './pages/WelcomePage';
import { SummaryViewing } from './pages/SummaryViewing';
import { Search } from 'lucide-react';
import { QnAPage } from './pages/QnAPage';
import GitHubContributions from './pages/github-contributions';


//{<div>Welcome! You are a viewing as a {user.role === 'dev' ? 'developer' : 'manager'} the repository {user.reponame}.</div>} />


const router = createBrowserRouter([
  {
    path: '/landing',
    element: <LandingPage />,
  },
  {
    path: '/signup',
    element: <SignupMain />,
  },
  {
    path: '/',
    element: <ProtectedLayout />,
    children: [
      {
        index: true,
        element: <WelcomePage />,
      },
      {
        path: '/summaryselection',
        element: <GitHubContributions />
      },
      {
        path: '/summaryviewing',
        element: <SummaryViewing />,
      },
      {
        path: '/search',
        element: <Search />,
      },
      {
        path: '/qna',
        element: <QnAPage />
      },
      {
        path: '/about',
        element: <About />
      }
    ],
  },
  {
    //path: '/:uuid', // Catch UUID URLs
    path: '/:uuid', // Catch UUID URLs
    element: <UUIDForwarder />,
  },
]);


function ProtectedLayout() {
  const { user, loading, api } = useAuth();
  return user ? <Header /> : <Navigate to="/landing" replace />;
}


function App() {

  return (

    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>

    /*
    <BrowserRouter> 
      <Routes>
          <Route index element={<LandingPage />} /> 
          <Route path="/about" element={ <About /> } />

          <Route path="view">
          <Route path="/selectcontent" element={ {selectcontent} } />
          <Route path="/summaryviewing" element={  {summaryviewing} } />
          <Route path="/questionandanswers" element= { { questionandanswers} } />
          <Route path="/search" element= { { search } } />
          
          <Route path="*" element = { <NoPage /> }
      </Routes>
    </BrowserRouter>   
    */
    



   
  );
}


export default App