// src/config/api.ts

// IMPORTANT:
// For local development, Flask runs on http://localhost:5000
// For production, set: VITE_API_BASE_URL="https://your-backend-url"

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

  export const API_ROUTES = {
    BUILDINGS: "https://urban-3d-dashboard.onrender.com/api/buildings",
    QUERY: "https://urban-3d-dashboard.onrender.com/api/query",
    HEALTH: "https://urban-3d-dashboard.onrender.com/api/health",
  };
