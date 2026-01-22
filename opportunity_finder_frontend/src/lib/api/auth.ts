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

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  role: string;
}

export interface ApiError {
  detail?: string;
  email?: string[];
  password?: string[];
  password2?: string[];
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

