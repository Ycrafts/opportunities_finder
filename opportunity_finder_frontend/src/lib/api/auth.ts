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

export interface User {
  id: number;
  email: string;
  is_active: boolean;
}

export interface ApiError {
  detail?: string;
  email?: string[];
  password?: string[];
  password2?: string[];
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

  extractError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiError>;
      return axiosError.response?.data || { detail: error.message };
    }
    return { detail: "An unexpected error occurred" };
  },
};

