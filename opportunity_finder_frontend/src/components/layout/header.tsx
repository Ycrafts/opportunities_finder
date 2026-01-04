"use client";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { config } from "@/lib/config";
import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
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

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
                    <DropdownMenuItem asChild>
                      <Link href="/dashboard">Dashboard</Link>
                    </DropdownMenuItem>
                    {user?.role === "ADMIN" && (
                      <DropdownMenuItem asChild>
                        <Link href="/admin">Admin Dashboard</Link>
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem asChild>
                      <Link href="/profile">Profile</Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => logout()}>
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
                      const authSection =
                        document.getElementById("get-started");
                      if (authSection) {
                        authSection.scrollIntoView({ behavior: "smooth" });
                        window.dispatchEvent(
                          new CustomEvent("auth-mode-change", {
                            detail: "login",
                          })
                        );
                      }
                    }}
                  >
                    Login
                  </Button>
                  <Button
                    onClick={() => {
                      const authSection =
                        document.getElementById("get-started");
                      if (authSection) {
                        authSection.scrollIntoView({ behavior: "smooth" });
                        window.dispatchEvent(
                          new CustomEvent("auth-mode-change", {
                            detail: "signup",
                          })
                        );
                      }
                    }}
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
