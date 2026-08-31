import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import QuantumNavOverlay from "./components/ui/quantum-nav-overlay.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <QuantumNavOverlay />
      <App />
    </BrowserRouter>
  </StrictMode>
);
