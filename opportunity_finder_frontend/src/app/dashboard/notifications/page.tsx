"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  Briefcase,
  LayoutDashboard,
  Settings,
  Sliders,
  Target,
  Users,
  Crown,
} from "lucide-react";
import { toast } from "sonner";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/animations/fade-in";
import { useAuth } from "@/contexts/auth-context";
import { notificationsApi, NotificationItem } from "@/lib/api/notifications";

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

const formatDate = (dateString?: string | null) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export default function NotificationsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  const { data: notifications = [], isLoading: isLoadingNotifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsApi.list,
    enabled: isAuthenticated,
  });

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: notificationsApi.unreadCount,
    enabled: isAuthenticated,
  });

  const markViewedMutation = useMutation({
    mutationFn: (notificationId: number) => notificationsApi.markViewed(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
    },
    onError: () => toast.error("Failed to mark notification as read."),
  });

  const markAllViewedMutation = useMutation({
    mutationFn: () => notificationsApi.markAllViewed(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
      toast.success("All notifications marked as read.");
    },
    onError: () => toast.error("Failed to mark all notifications as read."),
  });

  const navItemsWithBadge = navItems.map((item) =>
    item.title === "Notifications" ? { ...item, badge: unreadCount } : item
  );

  const sortedNotifications = [...notifications].sort((a, b) => {
    const aUnread = a.viewed_at ? 0 : 1;
    const bUnread = b.viewed_at ? 0 : 1;
    if (aUnread !== bUnread) return bUnread - aUnread;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
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

  const unreadLabel = unreadCount === 1 ? "unread" : "unread";

  return (
    <DashboardLayout navItems={navItemsWithBadge} title="Notifications">
      <div className="space-y-6 max-w-5xl">
        <FadeIn>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold">Notifications</h2>
              <p className="text-sm text-muted-foreground">
                {unreadCount} {unreadLabel} update{unreadCount === 1 ? "" : "s"}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={markAllViewedMutation.isPending || unreadCount === 0}
              onClick={() => markAllViewedMutation.mutate()}
            >
              Mark all read
            </Button>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <Card className="border-border/60">
            <CardHeader className="pb-4">
              <CardTitle className="text-base font-semibold">Recent updates</CardTitle>
              <CardDescription className="text-xs">
                All match notifications delivered to your dashboard
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoadingNotifications ? (
                <div className="text-sm text-muted-foreground">Loading notifications...</div>
              ) : notifications.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border/70 p-6 text-center text-sm text-muted-foreground">
                  No notifications yet.
                </div>
              ) : (
                sortedNotifications.map((notification: NotificationItem) => {
                  const isUnread = !notification.viewed_at;
                  const handleOpen = () => {
                    if (notification.opportunity_id) {
                      router.push(`/dashboard/opportunities/${notification.opportunity_id}`);
                    }
                    if (isUnread) {
                      markViewedMutation.mutate(notification.id);
                    }
                  };
                  return (
                    <div
                      key={notification.id}
                      role="button"
                      tabIndex={0}
                      onClick={handleOpen}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          handleOpen();
                        }
                      }}
                      className={`flex flex-col gap-3 rounded-lg border px-4 py-3 transition cursor-pointer ${
                        isUnread
                          ? "border-border/80 bg-muted/30"
                          : "border-border/60 bg-background"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">
                            {notification.subject || "New match update"}
                          </span>
                          {isUnread && (
                            <Badge variant="secondary" className="text-[10px]">
                              New
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(notification.created_at)}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">
                          {notification.organization}
                        </p>
                        <p className="text-sm">{notification.opportunity_title}</p>
                        {notification.message && (
                          <p className="text-xs text-muted-foreground">
                            {notification.message}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>Match score: {notification.match_details?.score ?? "-"}</span>
                        </div>
                        {isUnread && null}
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </DashboardLayout>
  );
}
