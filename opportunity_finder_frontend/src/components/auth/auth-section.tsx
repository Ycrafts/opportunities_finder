"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useAuth } from "@/contexts/auth-context";
import { authApi } from "@/lib/api/auth";
import { toast } from "sonner";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

const signupSchema = z
  .object({
    email: z.string().email("Please enter a valid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    password2: z.string(),
  })
  .refine((data) => data.password === data.password2, {
    message: "Passwords don't match",
    path: ["password2"],
  });

type LoginFormValues = z.infer<typeof loginSchema>;
type SignupFormValues = z.infer<typeof signupSchema>;

interface AuthSectionProps {
  defaultMode?: "login" | "signup";
}

export function AuthSection({ defaultMode = "login" }: AuthSectionProps) {
  const [mode, setMode] = useState<"login" | "signup">(defaultMode);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, register } = useAuth();

  useEffect(() => {
    setMode(defaultMode);
  }, [defaultMode]);

  useEffect(() => {
    const handleModeChange = (e: CustomEvent) => {
      setMode(e.detail as "login" | "signup");
    };

    window.addEventListener("auth-mode-change", handleModeChange as EventListener);
    return () => {
      window.removeEventListener("auth-mode-change", handleModeChange as EventListener);
    };
  }, []);

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const signupForm = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      email: "",
      password: "",
      password2: "",
    },
  });

  const onLoginSubmit = async (values: LoginFormValues) => {
    setIsSubmitting(true);
    try {
      await login({
        email: values.email,
        password: values.password,
      });
      toast.success("Welcome back! Redirecting...");
    } catch (error) {
      const apiError = authApi.extractError(error);
      // Handle different error formats from SimpleJWT
      const errorMessage = 
        apiError.detail || 
        apiError.non_field_errors?.[0] ||
        apiError.email?.[0] || 
        apiError.password?.[0] || 
        "Invalid email or password. Please try again.";
      toast.error(errorMessage);
      // Clear password field on error
      loginForm.setValue("password", "");
    } finally {
      setIsSubmitting(false);
    }
  };

  const onSignupSubmit = async (values: SignupFormValues) => {
    setIsSubmitting(true);
    try {
      await register({
        email: values.email,
        password: values.password,
        password2: values.password2,
      });
      toast.success("Account created! Redirecting...");
    } catch (error) {
      const apiError = authApi.extractError(error);
      // Handle different error formats
      const errorMessage = 
        apiError.detail || 
        apiError.non_field_errors?.[0] ||
        apiError.email?.[0] || 
        apiError.password?.[0] || 
        apiError.password2?.[0] || 
        "Registration failed. Please check your information and try again.";
      toast.error(errorMessage);
      
      // Set form errors for better UX
      if (apiError.email?.[0]) {
        signupForm.setError("email", { message: apiError.email[0] });
      }
      if (apiError.password?.[0]) {
        signupForm.setError("password", { message: apiError.password[0] });
      }
      if (apiError.password2?.[0]) {
        signupForm.setError("password2", { message: apiError.password2[0] });
      }
      
      // Clear passwords on error
      if (apiError.password?.[0] || apiError.password2?.[0]) {
        signupForm.setValue("password", "");
        signupForm.setValue("password2", "");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="relative bg-card/50 backdrop-blur-sm rounded-2xl border border-border/50 shadow-lg overflow-hidden">
        {/* Tab Switcher */}
        <div className="flex relative">
          <div
            className="absolute bottom-0 left-0 h-0.5 bg-primary transition-all duration-300 ease-out"
            style={{
              width: "50%",
              transform: mode === "login" ? "translateX(0)" : "translateX(100%)",
            }}
          />
          <button
            onClick={() => setMode("login")}
            className={`flex-1 px-8 py-5 text-sm font-semibold transition-all duration-200 relative ${
              mode === "login"
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setMode("signup")}
            className={`flex-1 px-8 py-5 text-sm font-semibold transition-all duration-200 relative ${
              mode === "signup"
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Forms Container */}
        <div className="relative overflow-hidden px-8 pb-8">
          <AnimatePresence mode="wait">
            {mode === "login" ? (
              <motion.div
                key="login"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="pt-8 pb-6">
                  <h3 className="text-2xl font-semibold tracking-tight mb-2">Welcome back</h3>
                  <p className="text-sm text-muted-foreground">
                    Enter your email and password to access your account.
                  </p>
                </div>
                <Form {...loginForm}>
                  <form
                    onSubmit={loginForm.handleSubmit(onLoginSubmit)}
                    className="space-y-5"
                  >
                      <FormField
                        control={loginForm.control}
                        name="email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-sm font-medium">Email</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="you@example.com"
                                className="h-11"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={loginForm.control}
                        name="password"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-sm font-medium">Password</FormLabel>
                            <FormControl>
                              <Input
                                type="password"
                                placeholder="••••••••"
                                className="h-11"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <Button 
                        type="submit" 
                        className="w-full h-11 mt-6" 
                        size="lg"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? "Logging in..." : "Login"}
                      </Button>
                      <div className="text-center text-sm text-muted-foreground">
                        <Link href="/forgot-password" className="hover:text-foreground">
                          Forgot password?
                        </Link>
                      </div>
                    </form>
                  </Form>
                </motion.div>
            ) : (
              <motion.div
                key="signup"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="pt-8 pb-6">
                  <h3 className="text-2xl font-semibold tracking-tight mb-2">Create Account</h3>
                  <p className="text-sm text-muted-foreground">
                    Sign up to start finding opportunities that match your profile.
                  </p>
                </div>
                <Form {...signupForm}>
                  <form
                    onSubmit={signupForm.handleSubmit(onSignupSubmit)}
                    className="space-y-5"
                  >
                      <FormField
                        control={signupForm.control}
                        name="email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-sm font-medium">Email</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="you@example.com"
                                className="h-11"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={signupForm.control}
                        name="password"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-sm font-medium">Password</FormLabel>
                            <FormControl>
                              <Input
                                type="password"
                                placeholder="••••••••"
                                className="h-11"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={signupForm.control}
                        name="password2"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-sm font-medium">Confirm Password</FormLabel>
                            <FormControl>
                              <Input
                                type="password"
                                placeholder="••••••••"
                                className="h-11"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <Button 
                        type="submit" 
                        className="w-full h-11 mt-6" 
                        size="lg"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? "Creating account..." : "Sign Up"}
                      </Button>
                    </form>
                  </Form>
                </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

