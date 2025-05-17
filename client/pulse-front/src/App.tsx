import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Button } from "@/components/ui/button"
import { useEffect, useRef } from "react";
import {ProfileForm } from "@/elements/landingform"






export function LandingPage() {

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Main Content (centered) */}
      <div className="flex flex-col items-center justify-center h-screen text-center px-4">
        <h1 className="text-3xl font-bold mb-3 text-gray-900">
        We help diverse teams keep up with others changes
        </h1>
        <p className="text-xl text-gray-600 max-w-md">
          Generate summaries from your weekly code progress with our LLM
        </p>
      </div>

      <div className="flex flex-col items-center justify-center min-h-svh">
        <ProfileForm></ProfileForm>
      </div>

    </div>
  );
}






function App() {
  const [count, setCount] = useState(0)


  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + ASDFASsadasdDF</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count fds is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
      sasadas
      {/* Adding a button */}
      {/* <div className="flex flex-col items-center justify-center min-h-svh">
      <Button>Click me</Button>
      </div> */}



    </>
  )
}

export default LandingPage
