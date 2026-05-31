import axios from "axios";

const BASE_URL = "https://cyber-exposure-platform.onrender.com";

const api = axios.create({
  baseURL: BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    console.error("API Error:", err.response?.status, err.config?.url);
    return Promise.reject(err);
  }
);

export const login = async (email, password) => {
  const res = await axios.post(`${BASE_URL}/auth/login`, { email, password });
  localStorage.setItem("token", res.data.access_token);
  localStorage.setItem("user", JSON.stringify(res.data.user));
  return res.data;
};

export const register = async (email, password, tenant_id, role = "viewer") => {
  const res = await axios.post(`${BASE_URL}/auth/register`, {
    email,
    password,
    tenant_id,
    role,
  });
  return res.data;
};

export const getMe = () => api.get("/auth/me");

export const getDashboardSummary = () => api.get("/dashboard/summary");
export const getDashboardAssets = () => api.get("/dashboard/assets");
export const getDashboardTopRisks = () => api.get("/dashboard/top-risks");
export const getScan = (hostname) => api.get(`/scan/${hostname}`);
export const getAssets = () => api.get("/assets");
export const getHealth = () => api.get("/health");
export const getFleetSummary = () => api.get("/fleet/summary");
export const getFleetAssets = () => api.get("/fleet/assets");
export const getFleetRiskTrends = () => api.get("/fleet/risk-trends");
export const getAlerts = () => api.get("/alerts");
export const ackAlert = (alert_id) => api.post("/alerts/acknowledge", { alert_id });
export const createTenant = (name, plan_type) => api.post("/tenants", { name, plan_type });
export const listTenants = () => api.get("/tenants");

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/login";
};

export const getUser = () => {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch {
    return null;
  }
};

export const isAuthenticated = () => !!localStorage.getItem("token");

export default api;
