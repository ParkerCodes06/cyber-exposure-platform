import axios from "axios";

const api = axios.create({
  baseURL: "https://cyber-exposure-platform.onrender.com",
});

api.interceptors.request.use((config) => {
  const key = localStorage.getItem("api_key");
  if (key) {
    config.headers["X-API-Key"] = key;
  }
  return config;
});

export const getDashboardSummary = () => api.get("/dashboard/summary");
export const getDashboardAssets = () => api.get("/dashboard/assets");
export const getDashboardTopRisks = () => api.get("/dashboard/top-risks");
export const getScan = (hostname) => api.get(`/scan/${hostname}`);
export const getAssets = () => api.get("/assets");
export const getHealth = () => api.get("/health");
export const getFleetSummary = () => api.get("/fleet/summary");
export const getFleetAssets = () => api.get("/fleet/assets");
export const getFleetRiskTrends = () => api.get("/fleet/risk-trends");

export default api;
