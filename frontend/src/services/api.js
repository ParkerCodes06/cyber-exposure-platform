import axios from "axios";

const BASE_URL = window.location.hostname === "localhost"
  ? "https://cyber-exposure-platform.onrender.com"
  : "";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401 && err.config && !err.config._retry) {
      err.config._retry = true;
      try {
        await axios.post(`${BASE_URL}/auth/refresh`, null, { withCredentials: true });
        return api(err.config);
      } catch {
        // Token expired, continue without auth — default tenant fallback
      }
    }
    return Promise.reject(err);
  }
);

export const login = async (email, password) => {
  const res = await axios.post(`${BASE_URL}/auth/login`, { email, password }, { withCredentials: true });
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

export const logout = async () => {
  try {
    await axios.post(`${BASE_URL}/auth/logout`, null, { withCredentials: true });
  } catch {
    // ignore
  }
  localStorage.removeItem("user");
  window.location.href = "/";
};

export const getUser = () => {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch {
    return null;
  }
};

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

export const isAuthenticated = () => !!localStorage.getItem("user");

export default api;
