"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Briefcase,
  LayoutDashboard,
  Sliders,
  Target,
  Users,
  Bell,
  Settings,
  Crown,
  BadgeCheck,
  UploadCloud,
} from "lucide-react";
import { toast } from "sonner";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
  { title: "Upgrade", href: "/dashboard/upgrade", icon: Crown },
];

export default function UpgradePage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [receipt, setReceipt] = useState<File | null>(null);
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  const { data: requests, isLoading: isLoadingRequests } = useQuery({
    queryKey: ["subscription-upgrade-requests"],
    queryFn: authApi.getSubscriptionUpgradeRequests,
    enabled: isAuthenticated,
  });

  const pendingRequest = useMemo(
    () => requests?.find((request) => request.status === "PENDING") ?? null,
    [requests]
  );

  const createRequestMutation = useMutation({
    mutationFn: () =>
      authApi.createSubscriptionUpgradeRequest({
        receipt,
        note,
      }),
    onSuccess: () => {
      toast.success("Upgrade request submitted. We'll review it shortly.");
      setReceipt(null);
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["subscription-upgrade-requests"] });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to submit upgrade request.";
      toast.error(message);
    },
  });

  if (isLoading || !isAuthenticated) {
    return null;
  }

  return (
    <DashboardLayout navItems={navItems} title="Upgrade">
      <div className="space-y-6 max-w-4xl">
        <FadeIn>
          <div>
            <h2 className="text-2xl font-semibold">Upgrade to Premium</h2>
            <p className="text-sm text-muted-foreground">
              Unlock unlimited cover letters and premium insights.
            </p>
          </div>
        </FadeIn>

        {user?.subscription_level === "PREMIUM" ? (
          <FadeIn delay={0.05}>
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <BadgeCheck className="h-4 w-4" />
                  You are Premium
                </CardTitle>
                <CardDescription className="text-xs">
                  Enjoy unlimited cover letter generations.
                </CardDescription>
              </CardHeader>
            </Card>
          </FadeIn>
        ) : (
          <>
            <FadeIn delay={0.05}>
              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base font-semibold">How it works</CardTitle>
                  <CardDescription className="text-xs">
                    Pay via Telebirr to 0932223954, upload your receipt, and we will approve within 24 hours.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  <p>1. Send payment to the official Telebirr account.</p>
                  <p>2. Upload your receipt screenshot or PDF.</p>
                  <p>3. Our admin team will approve or reject your request.</p>
                </CardContent>
              </Card>
            </FadeIn>

            <FadeIn delay={0.1}>
              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-semibold">
                    <UploadCloud className="h-4 w-4" />
                    Submit upgrade request
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Add payment proof to get approved.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="receipt">Receipt (screenshot or PDF)</Label>
                    <Input
                      id="receipt"
                      type="file"
                      accept="image/*,.pdf"
                      onChange={(event) =>
                        setReceipt(event.target.files ? event.target.files[0] : null)
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="note">Note (optional)</Label>
                    <Textarea
                      id="note"
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                      placeholder="Add any info to help verify your payment"
                      className="min-h-[100px]"
                    />
                  </div>
                  <Button
                    onClick={() => createRequestMutation.mutate()}
                    disabled={createRequestMutation.isPending || !receipt}
                  >
                    {createRequestMutation.isPending ? "Submitting..." : "Submit request"}
                  </Button>
                  {pendingRequest && (
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">Pending review</Badge>
                      Your request is under review.
                    </div>
                  )}
                </CardContent>
              </Card>
            </FadeIn>
          </>
        )}

        <FadeIn delay={0.15}>
          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Request history</CardTitle>
              <CardDescription className="text-xs">
                Track your past upgrade submissions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {isLoadingRequests ? (
                <p className="text-muted-foreground">Loading requests...</p>
              ) : !requests?.length ? (
                <p className="text-muted-foreground">No upgrade requests yet.</p>
              ) : (
                <div className="space-y-3">
                  {requests.map((requestItem) => (
                    <div
                      key={requestItem.id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2"
                    >
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">
                          {new Date(requestItem.created_at).toLocaleString()}
                        </p>
                        <p className="text-sm font-medium">{requestItem.payment_method}</p>
                        {requestItem.admin_note && (
                          <p className="text-xs text-muted-foreground">
                            Admin note: {requestItem.admin_note}
                          </p>
                        )}
                      </div>
                      <Badge
                        variant={
                          requestItem.status === "APPROVED"
                            ? "secondary"
                            : requestItem.status === "REJECTED"
                              ? "destructive"
                              : "outline"
                        }
                      >
                        {requestItem.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </DashboardLayout>
  );
}
