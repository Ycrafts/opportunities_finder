"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  Bell,
  Settings,
  Target,
  Sliders,
} from "lucide-react";
import { FadeIn } from "@/components/animations/fade-in";
import { useAuth } from "@/contexts/auth-context";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Opportunities", href: "/dashboard/opportunities", icon: Briefcase },
  { title: "Matches", href: "/dashboard/matches", icon: Target },
  { title: "Profile", href: "/dashboard/profile", icon: Users },
  { title: "Preferences", href: "/dashboard/preferences", icon: Sliders },
  { title: "Notifications", href: "/dashboard/notifications", icon: Bell, badge: 0 },
  { title: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

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
    <DashboardLayout navItems={navItems} title="Dashboard">
      <div className="space-y-8">
        {/* Welcome Section */}
        <FadeIn>
          <div className="space-y-1">
            <h2 className="text-3xl font-semibold tracking-tight">Dashboard</h2>
            <p className="text-sm text-muted-foreground">
              Here's an overview of your opportunities and activity.
            </p>
          </div>
        </FadeIn>

        {/* Stats Cards */}
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          <FadeIn delay={0.1}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Total Matches
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">0</div>
                <p className="text-xs font-normal text-muted-foreground">
                  Opportunities matched to you
                </p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.2}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Active Applications
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">0</div>
                <p className="text-xs font-normal text-muted-foreground">
                  Cover letters generated
                </p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.3}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Unread Notifications
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <Bell className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">0</div>
                <p className="text-xs font-normal text-muted-foreground">New updates for you</p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.4}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Profile Complete
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <Users className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">0%</div>
                <p className="text-xs font-normal text-muted-foreground">Complete your profile</p>
              </CardContent>
            </Card>
          </FadeIn>
        </div>

        {/* Recent Activity */}
        <div className="grid gap-5 md:grid-cols-2">
          <FadeIn delay={0.5}>
            <Card className="border-border/60">
              <CardHeader className="pb-4">
                <CardTitle className="text-base font-semibold">Recent Matches</CardTitle>
                <CardDescription className="text-xs mt-1">
                  Latest opportunities matched to your profile
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="mb-4 rounded-full bg-muted/50 p-3">
                    <Briefcase className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <p className="text-sm font-normal text-muted-foreground">
                    No matches yet. Complete your profile to get started.
                  </p>
                </div>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.6}>
            <Card className="border-border/60">
              <CardHeader className="pb-4">
                <CardTitle className="text-base font-semibold">Quick Actions</CardTitle>
                <CardDescription className="text-xs mt-1">Get started with these actions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <div className="group rounded-lg border border-border/60 p-3.5 hover:border-border hover:bg-muted/30 transition-all cursor-pointer">
                  <div className="font-medium text-sm mb-0.5">Complete Your Profile</div>
                  <div className="text-xs font-normal text-muted-foreground">
                    Add your skills and preferences
                  </div>
                </div>
                <div className="group rounded-lg border border-border/60 p-3.5 hover:border-border hover:bg-muted/30 transition-all cursor-pointer">
                  <div className="font-medium text-sm mb-0.5">Upload Your CV</div>
                  <div className="text-xs font-normal text-muted-foreground">
                    Let AI extract your information
                  </div>
                </div>
                <div className="group rounded-lg border border-border/60 p-3.5 hover:border-border hover:bg-muted/30 transition-all cursor-pointer">
                  <div className="font-medium text-sm mb-0.5">Browse Opportunities</div>
                  <div className="text-xs font-normal text-muted-foreground">
                    Explore available opportunities
                  </div>
                </div>
              </CardContent>
            </Card>
          </FadeIn>
        </div>
      </div>
    </DashboardLayout>
  );
}

