"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Settings,
  BarChart3,
  Shield,
  Database,
} from "lucide-react";
import { FadeIn } from "@/components/animations/fade-in";
import { useAuth } from "@/contexts/auth-context";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

const adminNavItems = [
  { title: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { title: "Users", href: "/admin/users", icon: Users },
  { title: "Opportunities", href: "/admin/opportunities", icon: Briefcase },
  { title: "Sources", href: "/admin/sources", icon: Database },
  { title: "Analytics", href: "/admin/analytics", icon: BarChart3 },
  { title: "Settings", href: "/admin/settings", icon: Settings },
];

export default function AdminDashboardPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    } else if (user && user.role !== "ADMIN") {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated || user?.role !== "ADMIN") {
    return null;
  }

  return (
    <DashboardLayout navItems={adminNavItems} title="Admin Dashboard">
      <div className="space-y-6">
        {/* Welcome Section */}
        <FadeIn>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Admin Dashboard</h2>
            <p className="text-muted-foreground">Manage users, opportunities, and system settings.</p>
          </div>
        </FadeIn>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <FadeIn delay={0.1}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">-</div>
                <p className="text-xs text-muted-foreground">Registered users</p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.2}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Opportunities</CardTitle>
                <Briefcase className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">-</div>
                <p className="text-xs text-muted-foreground">Total opportunities</p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.3}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Matches</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">-</div>
                <p className="text-xs text-muted-foreground">Matches created</p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.4}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Status</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">-</div>
                <p className="text-xs text-muted-foreground">All systems operational</p>
              </CardContent>
            </Card>
          </FadeIn>
        </div>

        {/* Admin Sections */}
        <div className="grid gap-4 md:grid-cols-2">
          <FadeIn delay={0.5}>
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>Manage user accounts and permissions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Users className="mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    User management features coming soon
                  </p>
                </div>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.6}>
            <Card>
              <CardHeader>
                <CardTitle>System Analytics</CardTitle>
                <CardDescription>View system metrics and reports</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <BarChart3 className="mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Analytics dashboard coming soon
                  </p>
                </div>
              </CardContent>
            </Card>
          </FadeIn>
        </div>
      </div>
    </DashboardLayout>
  );
}

