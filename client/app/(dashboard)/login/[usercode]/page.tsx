"use client";

import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useUser } from "@/contexts/user-context";

interface LoginPageProps {
  params: {
    usercode: string;
  };
}

export default function LoginPage({ params }: LoginPageProps) {
  const { usercode } = params;
  const { setUserId } = useUser();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const loginUser = async () => {
      try {
        // Validate usercode format (basic validation)
        if (!usercode || usercode.length < 1) {
          throw new Error("Invalid user code");
        }

        // Decode the usercode if it's URL encoded
        const decodedUsercode = decodeURIComponent(usercode);

        // Set the user ID using our hook
        setUserId(decodedUsercode);

        // Show success state briefly
        setStatus("success");

        // Redirect to dashboard after a short delay
        setTimeout(() => {
          router.push("/dashboard");
        }, 1500);
      } catch (error) {
        console.error("Login error:", error);
        setStatus("error");
        setErrorMessage(error instanceof Error ? error.message : "An unknown error occurred");
      }
    };

    loginUser();
  }, [usercode, setUserId, router]);

  const handleRetry = () => {
    setStatus("loading");
    setErrorMessage("");
    // Trigger the login process again
    setTimeout(() => {
      try {
        const decodedUsercode = decodeURIComponent(usercode);
        setUserId(decodedUsercode);
        setStatus("success");
        setTimeout(() => {
          router.push("/dashboard");
        }, 1500);
      } catch (error) {
        setStatus("error");
        setErrorMessage(error instanceof Error ? error.message : "An unknown error occurred");
      }
    }, 500);
  };

  const handleGoToDashboard = () => {
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Logging you in...</h2>
          <p className="mt-2 text-sm text-gray-600">
            Setting up your session with user code:{" "}
            <code className="bg-gray-100 px-2 py-1 rounded text-xs">{usercode}</code>
          </p>
        </div>

        <Card className="mt-8">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2">
              {status === "loading" && (
                <>
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                  Authenticating
                </>
              )}
              {status === "success" && (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  Login Successful
                </>
              )}
              {status === "error" && (
                <>
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  Login Failed
                </>
              )}
            </CardTitle>
            <CardDescription>
              {status === "loading" && "Please wait while we set up your account..."}
              {status === "success" && "Redirecting you to the dashboard..."}
              {status === "error" && "There was an issue with your login"}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            {status === "loading" && (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                </div>
                <p className="text-sm text-gray-500">This should only take a moment...</p>
              </div>
            )}

            {status === "success" && (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <CheckCircle className="h-12 w-12 text-green-600" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">
                    Welcome! Your session has been established.
                  </p>
                  <p className="text-xs text-gray-500">
                    You'll be redirected automatically in a moment.
                  </p>
                </div>
                <Button className="w-full" onClick={handleGoToDashboard}>
                  Go to Dashboard Now
                </Button>
              </div>
            )}

            {status === "error" && (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <AlertCircle className="h-12 w-12 text-red-600" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-red-600 font-medium">{errorMessage}</p>
                  <p className="text-xs text-gray-500">Please check your URL and try again.</p>
                </div>
                <div className="flex gap-2">
                  <Button className="flex-1" onClick={handleRetry} variant="outline">
                    Try Again
                  </Button>
                  <Button className="flex-1" onClick={handleGoToDashboard}>
                    Continue Anyway
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            Having trouble? Contact support or try accessing the dashboard directly.
          </p>
        </div>
      </div>
    </div>
  );
}
