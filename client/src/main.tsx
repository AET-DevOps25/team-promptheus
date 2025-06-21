import { StrictMode } from "react";
//import { createRoot } from 'react-dom/client'
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

// biome-ignore lint/style/noNonNullAssertion: any other handling of this would be more complex and unnecessary
ReactDOM.createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<App />
	</StrictMode>,
);
