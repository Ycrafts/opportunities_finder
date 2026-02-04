"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import {
  authApi,
  type User,
  type LoginRequest,
  type RegisterRequest,
} from "@/lib/api/auth";
import {
  consumePostAuthRedirect,
  sanitizeInternalRedirectPath,
} from "@/lib/auth/post-auth-redirect";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const refreshUser = async (): Promise<User | null> => {
    try {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        setUser(null);
        setIsLoading(false);
        return null;
      }

      const userData = await authApi.getMe();
      setUser(userData);
      return userData;
    } catch (error) {
      // Token invalid or expired
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setUser(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (data: LoginRequest): Promise<void> => {
    try {
      const response = await authApi.login(data);
      localStorage.setItem("access_token", response.access);
      localStorage.setItem("refresh_token", response.refresh);
      const userData = await refreshUser();
      const redirect = sanitizeInternalRedirectPath(consumePostAuthRedirect());
      if (redirect) {
        router.push(redirect);
        return;
      }
      // Redirect based on user role
      if (userData?.role === "ADMIN") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (error) {
      // Re-throw error so it can be caught and handled by the component
      throw error;
    }
  };

  const register = async (data: RegisterRequest): Promise<void> => {
    try {
      await authApi.register(data);
      // After registration, automatically log in
      await login({ email: data.email, password: data.password });
    } catch (error) {
      // Re-throw error so it can be caught and handled by the component
      throw error;
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch (error) {
        // Even if logout fails, clear local storage
        console.error("Logout error:", error);
      }
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    router.push("/");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
