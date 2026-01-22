"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import {
  Bell,
  Briefcase,
  LayoutDashboard,
  Settings,
  Sliders,
  Target,
  Users,
  LogOut,
  KeyRound,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FadeIn } from "@/components/animations/fade-in";
import { useAuth } from "@/contexts/auth-context";
import { authApi } from "@/lib/api/auth";

const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Opportunities", href: "/dashboard/opportunities", icon: Briefcase },
  { title: "Matches", href: "/dashboard/matches", icon: Target },
  { title: "Profile", href: "/dashboard/profile", icon: Users },
  { title: "Preferences", href: "/dashboard/preferences", icon: Sliders },
  { title: "Notifications", href: "/dashboard/notifications", icon: Bell, badge: 0 },
  { title: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function SettingsPage() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const [deletePassword, setDeletePassword] = useState("");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  const passwordMutation = useMutation({
    mutationFn: () => authApi.changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    }),
    onSuccess: () => {
      toast.success("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (error) => {
      const details = authApi.extractError(error);
      const message = details.current_password?.[0] || details.new_password?.[0] || details.detail || "Failed to update password.";
      toast.error(message);
    },
  });

  const logoutAllMutation = useMutation({
    mutationFn: () => authApi.logoutAll(),
    onSuccess: async () => {
      toast.success("Signed out of all devices.");
      await logout();
    },
    onError: () => toast.error("Failed to log out all sessions."),
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => authApi.deleteAccount({
      password: deletePassword,
      confirm: confirmText,
    }),
    onSuccess: () => {
      toast.success("Account deleted.");
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      router.push("/");
    },
    onError: (error) => {
      const details = authApi.extractError(error);
      const message = details.password?.[0] || details.confirm?.[0] || details.detail || "Failed to delete account.";
      toast.error(message);
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <DashboardLayout navItems={navItems} title="Settings">
      <div className="space-y-6 max-w-4xl">
        <FadeIn>
          <div>
            <h2 className="text-2xl font-semibold">Account settings</h2>
            <p className="text-sm text-muted-foreground">
              Manage access, security, and account lifecycle for {user?.email}.
            </p>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <KeyRound className="h-4 w-4" />
                Change password
              </CardTitle>
              <CardDescription className="text-xs">
                Update your password. You will stay signed in on this device.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current-password">Current password</Label>
                <Input
                  id="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm new password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                />
              </div>
              <Button
                onClick={() => {
                  if (newPassword !== confirmPassword) {
                    toast.error("Passwords do not match.");
                    return;
                  }
                  passwordMutation.mutate();
                }}
                disabled={
                  !currentPassword ||
                  !newPassword ||
                  !confirmPassword ||
                  passwordMutation.isPending
                }
              >
                {passwordMutation.isPending ? "Updating..." : "Update password"}
              </Button>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn delay={0.2}>
          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <LogOut className="h-4 w-4" />
                Sessions
              </CardTitle>
              <CardDescription className="text-xs">
                End active sessions across devices.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3">
              <Button variant="outline" onClick={() => logout()}>
                Sign out of this device
              </Button>
              <Button
                variant="secondary"
                onClick={() => logoutAllMutation.mutate()}
                disabled={logoutAllMutation.isPending}
              >
                {logoutAllMutation.isPending ? "Signing out..." : "Sign out everywhere"}
              </Button>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn delay={0.3}>
          <Card className="border-destructive/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-destructive">
                <ShieldAlert className="h-4 w-4" />
                Danger zone
              </CardTitle>
              <CardDescription className="text-xs">
                Delete your account and all associated data. This cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="delete-password">Confirm with password</Label>
                  <Input
                    id="delete-password"
                    type="password"
                    value={deletePassword}
                    onChange={(event) => setDeletePassword(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="delete-confirm">Type DELETE</Label>
                  <Input
                    id="delete-confirm"
                    placeholder="DELETE"
                    value={confirmText}
                    onChange={(event) => setConfirmText(event.target.value)}
                  />
                </div>
              </div>
              <Button
                variant="destructive"
                onClick={() => deleteAccountMutation.mutate()}
                disabled={!deletePassword || !confirmText || deleteAccountMutation.isPending}
              >
                {deleteAccountMutation.isPending ? "Deleting..." : "Delete account"}
              </Button>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </DashboardLayout>
  );
}
