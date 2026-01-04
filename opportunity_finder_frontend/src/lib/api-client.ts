import axios, { AxiosError, AxiosInstance } from "axios";

// Get API URL from environment or detect from current host
const getApiBaseUrl = (): string => {
  // Use environment variable if set
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // In browser, detect the current host and use it for backend
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    // If accessing from localhost, use localhost for backend
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://localhost:8000";
    }
    // Otherwise, use the same host with port 8000
    return `http://${host}:8000`;
  }
  
  // Server-side fallback
  return "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Don't try to refresh token for auth endpoints (login, register, refresh)
    const isAuthEndpoint = originalRequest?.url?.includes("/auth/token/") || 
                           originalRequest?.url?.includes("/auth/register/") ||
                           originalRequest?.url?.includes("/auth/token/refresh/");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
          throw new Error("No refresh token");
        }

        const response = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem("access_token", access);
        originalRequest.headers.Authorization = `Bearer ${access}`;

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

