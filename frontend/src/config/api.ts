// src/config/api.ts

// IMPORTANT:
// For local development, Flask runs on http://localhost:5000
// For production, set: VITE_API_BASE_URL="https://your-backend-url"

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export const API_ROUTES = {
  HEALTH: `${API_BASE_URL}/api/health`,
  BUILDINGS: `${API_BASE_URL}/api/buildings`,
  QUERY: `${API_BASE_URL}/api/query`,
};
