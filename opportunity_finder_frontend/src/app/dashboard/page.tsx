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
  Crown,
} from "lucide-react";
import { FadeIn } from "@/components/animations/fade-in";
import { useAuth } from "@/contexts/auth-context";
import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import { matchesApi } from "@/lib/api/matches";
import Link from "next/link";
import { profileApi } from "@/lib/api/profile";

const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Opportunities", href: "/dashboard/opportunities", icon: Briefcase },
  { title: "Matches", href: "/dashboard/matches", icon: Target },
  { title: "Profile", href: "/dashboard/profile", icon: Users },
  { title: "Preferences", href: "/dashboard/preferences", icon: Sliders },
  { title: "Notifications", href: "/dashboard/notifications", icon: Bell, badge: 0 },
  { title: "Settings", href: "/dashboard/settings", icon: Settings },
  { title: "Upgrade", href: "/dashboard/upgrade", icon: Crown },
];

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const { data: dashboardStats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: authApi.getDashboardStats,
    enabled: isAuthenticated,
  });

  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: profileApi.getProfile,
    enabled: isAuthenticated,
  });

  const { data: matches } = useQuery({
    queryKey: ["recent-matches"],
    queryFn: () => matchesApi.list("ACTIVE"),
    enabled: isAuthenticated,
  });

  const profileCompletion = useMemo(() => {
    if (!profile) return 0;
    const checks = [
      Boolean(profile.full_name?.trim()),
      Boolean(profile.cv_text?.trim() || profile.cv_file),
      Boolean(profile.skills?.length),
      Boolean(profile.interests?.length),
      Boolean(profile.languages?.length),
      Boolean(
        profile.academic_info &&
          (profile.academic_info.degree ||
            profile.academic_info.university ||
            profile.academic_info.degrees?.length)
      ),
    ];
    const total = checks.length;
    const completed = checks.filter(Boolean).length;
    return Math.round((completed / total) * 100);
  }, [profile]);

  const popularDomains = useMemo(() => {
    const items = dashboardStats?.popular_domains ?? [];
    const total = items.reduce((sum, item) => sum + (item.count ?? 0), 0);
    return {
      total,
      items: items
        .filter((item) => item.count > 0)
        .map((item) => ({
          name: item.name ?? "Other",
          count: item.count,
        })),
    };
  }, [dashboardStats?.popular_domains]);

  const recentMatches = useMemo(() => {
    if (!matches?.length) return [];
    return [...matches]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 3);
  }, [matches]);

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
    <DashboardLayout navItems={navItems}>
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

        {/* Recent Activity */}
        <div className="grid gap-5 md:grid-cols-2">
          <FadeIn delay={0.5}>
            <Card className="border-border/60">
              <CardHeader className="pb-4">
                <CardTitle className="text-base font-semibold">Quick Actions</CardTitle>
                <CardDescription className="text-xs mt-1">Get started with these actions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <Link
                  href="/dashboard/profile"
                  className="group block w-full rounded-lg border border-border/60 p-3.5 hover:border-border hover:bg-muted/30 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="font-medium text-sm">Complete Your Profile</div>
                    <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground tabular-nums">
                      {profileCompletion}%
                    </span>
                  </div>
                  <div className="text-xs font-normal text-muted-foreground">
                    Add your skills and preferences
                  </div>
                </Link>
                <Link
                  href="/dashboard/profile#cv_file"
                  className="group block w-full rounded-lg border border-border/60 p-3.5 hover:border-border hover:bg-muted/30 transition-all"
                >
                  <div className="font-medium text-sm mb-0.5">Upload Your CV</div>
                  <div className="text-xs font-normal text-muted-foreground">
                    Let AI extract your information
                  </div>
                </Link>
                <Link
                  href="/dashboard/opportunities"
                  className="group block w-full rounded-lg border border-border/60 p-3.5 hover:border-border hover:bg-muted/30 transition-all"
                >
                  <div className="font-medium text-sm mb-0.5">Browse Opportunities</div>
                  <div className="text-xs font-normal text-muted-foreground">
                    Explore available opportunities
                  </div>
                </Link>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.6}>
            <Card className="border-border/60">
              <CardHeader className="pb-4">
                <CardTitle className="text-base font-semibold">Recent Matches</CardTitle>
                <CardDescription className="text-xs mt-1">
                  Latest opportunities matched to your profile
                </CardDescription>
              </CardHeader>
              <CardContent>
                {recentMatches.length ? (
                  <div className="space-y-3">
                    {recentMatches.map((match) => (
                      <Link
                        key={match.id}
                        href={`/dashboard/opportunities/${match.opportunity.id}`}
                        className="flex items-center justify-between gap-3 rounded-lg border border-border/60 p-3 transition hover:border-border hover:bg-muted/30"
                      >
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-foreground">
                            {match.opportunity.title}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {match.opportunity.organization || "Unknown organization"}
                          </div>
                        </div>
                        <div className="text-xs font-semibold text-foreground">
                          {match.match_score ? match.match_score.toFixed(1) : "-"}
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="mb-4 rounded-full bg-muted/50 p-3">
                      <Briefcase className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="text-sm font-normal text-muted-foreground">
                      No matches yet. Complete your profile to get started.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </FadeIn>
        </div>

        <FadeIn delay={0.45}>
          <Card className="border-border/60">
            <CardHeader className="pb-4">
              <CardTitle className="text-base font-semibold">Market demand</CardTitle>
              <CardDescription className="text-xs mt-1">
                Most popular opportunity domains (last 30 days)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-4 rounded-lg border border-border/60 bg-muted/20 p-4 text-muted-foreground dark:text-white md:flex-row md:items-center md:gap-6">
                <div className="relative h-44 w-44 shrink-0">
                  <svg viewBox="0 0 120 120" className="h-full w-full">
                    <circle
                      cx="60"
                      cy="60"
                      r="42"
                      stroke="currentColor"
                      strokeOpacity="0.15"
                      strokeWidth="14"
                      fill="none"
                    />
                    {(() => {
                      const radius = 42;
                      const circumference = 2 * Math.PI * radius;
                      let offset = 0;
                      const colors = [
                        "#f97316",
                        "#22c55e",
                        "#3b82f6",
                        "#eab308",
                        "#a855f7",
                      ];
                      return popularDomains.items.map((item, index) => {
                        const fraction = popularDomains.total
                          ? item.count / popularDomains.total
                          : 0;
                        const dash = fraction * circumference;
                        const strokeDasharray = `${dash} ${circumference - dash}`;
                        const strokeDashoffset = -offset;
                        offset += dash;
                        return (
                          <circle
                            key={item.name}
                            cx="60"
                            cy="60"
                            r={radius}
                            stroke={colors[index % colors.length]}
                            strokeWidth="14"
                            fill="none"
                            strokeDasharray={strokeDasharray}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="round"
                          />
                        );
                      });
                    })()}
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="text-xs uppercase tracking-wide text-muted-foreground dark:text-white/70">
                      Total
                    </span>
                    <span className="text-2xl font-semibold text-foreground dark:text-white">
                      {popularDomains.total || 0}
                    </span>
                  </div>
                </div>
                <div className="flex-1 space-y-2">
                  {popularDomains.items.length ? (
                    popularDomains.items.map((item, index) => (
                      <div key={item.name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span
                            className="h-2.5 w-2.5 rounded-full"
                            style={{
                              backgroundColor:
                                ["#f97316", "#22c55e", "#3b82f6", "#eab308", "#a855f7"][
                                  index % 5
                                ],
                            }}
                          />
                          <span className="text-sm text-foreground dark:text-white">
                            {item.name}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-foreground dark:text-white">
                          {popularDomains.total
                            ? `${Math.round((item.count / popularDomains.total) * 100)}%`
                            : "0%"}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-muted-foreground dark:text-white/70">
                      No demand data available yet.
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Stats Cards */}
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          <FadeIn delay={0.1}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  New Opportunities
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <Briefcase className="h-3.5 w-3.5 text-[#0f9b57]" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">
                  {dashboardStats
                    ? `${dashboardStats.new_opportunities_last_7_days} / ${dashboardStats.new_opportunities_last_30_days}`
                    : "-"}
                </div>
                <p className="text-xs font-normal text-muted-foreground">
                  Last 7 / 30 days
                </p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.2}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Matches Generated
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <FileText className="h-3.5 w-3.5 text-[#0f9b57]" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">
                  {dashboardStats
                    ? `${dashboardStats.matches_total} / ${dashboardStats.matches_last_7_days}`
                    : "-"}
                </div>
                <p className="text-xs font-normal text-muted-foreground">
                  Total and this week
                </p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.3}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Active Matches
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <Bell className="h-3.5 w-3.5 text-[#0f9b57]" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">
                  {dashboardStats
                    ? `${dashboardStats.active_matches ?? 0}`
                    : "-"}
                </div>
                <p className="text-xs font-normal text-muted-foreground">
                  Opportunities currently active
                </p>
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.4}>
            <Card className="border-border/60">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Cover Letters Used
                </CardTitle>
                <div className="rounded-md bg-muted/50 p-1.5">
                  <Users className="h-3.5 w-3.5 text-[#0f9b57]" />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="number-display text-3xl font-semibold">
                  {dashboardStats
                    ? `${dashboardStats.cover_letters_monthly_count}${
                        dashboardStats.cover_letters_monthly_limit
                          ? ` / ${dashboardStats.cover_letters_monthly_limit}`
                          : ""
                      }`
                    : "-"}
                </div>
                <p className="text-xs font-normal text-muted-foreground">
                  Usage vs monthly limit
                </p>
              </CardContent>
            </Card>
          </FadeIn>
        </div>
      </div>
    </DashboardLayout>
  );
}

