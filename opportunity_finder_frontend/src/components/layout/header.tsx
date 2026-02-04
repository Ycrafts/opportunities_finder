"use client";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { config } from "@/lib/config";
import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { LogOut } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const { isAuthenticated, user, logout, isLoading } = useAuth();

  const scrollToAuthSection = (mode: "login" | "signup") => {
    const authSection = document.getElementById("get-started");
    if (!authSection) return;
    const offset = 180;
    const top = authSection.getBoundingClientRect().top + window.scrollY + offset;
    window.scrollTo({ top, behavior: "smooth" });
    window.dispatchEvent(new CustomEvent("auth-mode-change", { detail: mode }));
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full bg-transparent border-0 backdrop-blur-0 supports-[backdrop-filter]:bg-transparent">
      <motion.div
        className="container flex h-16 items-center justify-between px-4"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-2">
          <Link
            href="/"
            className="text-xl font-semibold hover:opacity-80 transition-opacity"
          >
            {config.app.name}
          </Link>
        </div>
        <nav className="flex items-center gap-4">
          <ThemeToggle />
          {config.features.enableAuth && !isLoading && (
            <>
              {isAuthenticated ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="gap-2">
                      <span className="hidden sm:inline">{user?.email}</span>
                      <span className="sm:hidden">Account</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => logout()}>
                      <LogOut className="h-4 w-4" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    className="hidden sm:inline-flex"
                    onClick={() => {
                      scrollToAuthSection("login");
                    }}
                  >
                    Login
                  </Button>
                  <Button
                    onClick={() => {
                      scrollToAuthSection("signup");
                    }}
                    className="bg-[#0f9b57] hover:bg-[#0d884d]"
                  >
                    Get Started
                  </Button>
                </>
              )}
            </>
          )}
        </nav>
      </motion.div>
    </header>
  );
}
