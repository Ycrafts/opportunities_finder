"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";

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

function LoginPageContent() {
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<"login" | "signup">("login");

  useEffect(() => {
    const modeParam = searchParams.get("mode");
    if (modeParam === "signup") {
      setMode("signup");
    }
  }, [searchParams]);

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
    // TODO: Implement API call
    console.log("Login:", values);
  };

  const onSignupSubmit = async (values: SignupFormValues) => {
    // TODO: Implement API call
    console.log("Signup:", values);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <Link
            href="/"
            className="mb-8 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>

        <Card className="relative overflow-hidden">
          <div className="relative">
            {/* Tab Switcher */}
            <div className="flex border-b">
              <button
                onClick={() => setMode("login")}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                  mode === "login"
                    ? "text-foreground border-b-2 border-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setMode("signup")}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                  mode === "signup"
                    ? "text-foreground border-b-2 border-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Forms Container */}
            <div className="relative overflow-hidden">
              <AnimatePresence mode="wait">
                {mode === "login" ? (
                  <motion.div
                    key="login"
                    initial={{ x: -300, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: 300, opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <CardHeader>
                      <CardTitle>Welcome back</CardTitle>
                      <CardDescription>
                        Enter your email and password to access your account.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Form {...loginForm}>
                        <form
                          onSubmit={loginForm.handleSubmit(onLoginSubmit)}
                          className="space-y-4"
                        >
                          <FormField
                            control={loginForm.control}
                            name="email"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Email</FormLabel>
                                <FormControl>
                                  <Input
                                    type="email"
                                    placeholder="you@example.com"
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
                                <FormLabel>Password</FormLabel>
                                <FormControl>
                                  <Input
                                    type="password"
                                    placeholder="••••••••"
                                    {...field}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <Button type="submit" className="w-full">
                            Login
                          </Button>
                        </form>
                      </Form>
                    </CardContent>
                  </motion.div>
                ) : (
                  <motion.div
                    key="signup"
                    initial={{ x: 300, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: -300, opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <CardHeader>
                      <CardTitle>Create Account</CardTitle>
                      <CardDescription>
                        Sign up to start finding opportunities that match your profile.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Form {...signupForm}>
                        <form
                          onSubmit={signupForm.handleSubmit(onSignupSubmit)}
                          className="space-y-4"
                        >
                          <FormField
                            control={signupForm.control}
                            name="email"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Email</FormLabel>
                                <FormControl>
                                  <Input
                                    type="email"
                                    placeholder="you@example.com"
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
                                <FormLabel>Password</FormLabel>
                                <FormControl>
                                  <Input
                                    type="password"
                                    placeholder="••••••••"
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
                                <FormLabel>Confirm Password</FormLabel>
                                <FormControl>
                                  <Input
                                    type="password"
                                    placeholder="••••••••"
                                    {...field}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <Button type="submit" className="w-full">
                            Sign Up
                          </Button>
                        </form>
                      </Form>
                    </CardContent>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </Card>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen flex-col">
        <Header />
        <div className="flex flex-1 items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </div>
    }>
      <LoginPageContent />
    </Suspense>
  );
}

