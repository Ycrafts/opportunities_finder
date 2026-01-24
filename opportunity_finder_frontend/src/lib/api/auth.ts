import axios, { type AxiosError } from "axios";
import apiClient from "../api-client";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password2: string;
}

export interface RegisterResponse {
  id: number;
  email: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface DeleteAccountRequest {
  password: string;
  confirm: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  uid: string;
  token: string;
  new_password: string;
  new_password2: string;
}

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  role: string;
  subscription_level: "STANDARD" | "PREMIUM";
}

export interface SubscriptionUpgradeRequest {
  id: number;
  status: "PENDING" | "APPROVED" | "REJECTED";
  payment_method: string;
  receipt: string;
  note: string;
  admin_note: string;
  reviewed_at: string | null;
  created_at: string;
}

export interface SubscriptionUpgradeCreateRequest {
  receipt?: File | null;
  note?: string;
}

export interface DashboardStats {
  new_opportunities_last_7_days: number;
  new_opportunities_last_30_days: number;
  opportunities_weekly: Array<{ week_start: string | null; count: number }>;
  popular_domains: Array<{ name: string | null; count: number }>;
  matches_total: number;
  matches_last_7_days: number;
  active_matches: number;
  cover_letters_monthly_count: number;
  cover_letters_monthly_limit: number | null;
}

export interface ApiError {
  detail?: string;
  email?: string[];
  password?: string[];
  password2?: string[];
  new_password?: string[];
  non_field_errors?: string[];
  [key: string]: any;
}

export const authApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>("/auth/token/", {
      email: data.email,
      password: data.password,
    });
    return response.data;
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>("/auth/register/", {
      email: data.email,
      password: data.password,
      password2: data.password2,
    });
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>("/auth/me/");
    return response.data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout/", { refresh: refreshToken });
  },

  async logoutAll(): Promise<void> {
    await apiClient.post("/auth/logout/all/");
  },

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiClient.post("/auth/password/change/", data);
  },

  async deleteAccount(data: DeleteAccountRequest): Promise<void> {
    await apiClient.post("/auth/account/delete/", data);
  },

  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    await apiClient.post("/auth/password/reset/", data);
  },

  async confirmPasswordReset(data: PasswordResetConfirmRequest): Promise<void> {
    await apiClient.post("/auth/password/reset/confirm/", data);
  },

  async getSubscriptionUpgradeRequests(): Promise<SubscriptionUpgradeRequest[]> {
    const response = await apiClient.get<{ results: SubscriptionUpgradeRequest[] }>(
      "/auth/subscription/requests/"
    );
    return response.data.results ?? [];
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>("/auth/dashboard/stats/");
    return response.data;
  },

  async createSubscriptionUpgradeRequest(
    data: SubscriptionUpgradeCreateRequest
  ): Promise<SubscriptionUpgradeRequest> {
    const formData = new FormData();
    if (data.note) {
      formData.append("note", data.note);
    }
    if (data.receipt) {
      formData.append("receipt", data.receipt);
    }
    const response = await apiClient.post<SubscriptionUpgradeRequest>(
      "/auth/subscription/requests/",
      formData
    );
    return response.data;
  },

  extractError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiError>;
      const errorData = axiosError.response?.data;

      // If we have error data, return it
      if (errorData) {
        return errorData;
      }

      // If no response but we have a message, use it
      if (error.message) {
        return { detail: error.message };
      }

      // Network error or other axios errors
      if (error.code === "ERR_NETWORK") {
        return { detail: "Network error. Please check your connection." };
      }

      return { detail: "An unexpected error occurred" };
    }
    return { detail: "An unexpected error occurred" };
  },
};

