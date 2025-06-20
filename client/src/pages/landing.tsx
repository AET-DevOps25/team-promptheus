import { Button } from "@/components/ui/button";
import { Navigate, useNavigate } from "react-router-dom";




export function LandingPage() {

  const navigate = useNavigate()

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
  
        <div className="card">

          <Button onClick={() => navigate('/signup')}> 
            Get started
          </Button>
          {/* <p>
            Edit <code>src/App.tsx</code> and save to test HMR
          </p> */}
        </div>
  
  
      </div>
    );
  }
  
export default LandingPage