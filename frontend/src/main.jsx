import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom";

import App from "./App.jsx"
import { AuthProvider } from "./contexts/AuthContext";
import { TutorialProvider } from "./contexts/TutorialContext";

import "./styles/index.css"


createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <TutorialProvider>
          <App />
        </TutorialProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
