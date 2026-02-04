"use client";

import { Header } from "@/components/layout/header";
import { FadeIn } from "@/components/animations/fade-in";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { opportunitiesApi } from "@/lib/api/opportunities";
import { setPostAuthRedirect } from "@/lib/auth/post-auth-redirect";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { useParams } from "next/navigation";
import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ExternalLink,
  FileText,
  Sparkles,
  Target,
  MapPin,
  Calendar,
  Lock,
} from "lucide-react";

const formatWorkMode = (mode: string) => {
  const modes: Record<string, string> = {
    REMOTE: "Remote",
    ONSITE: "Onsite",
    HYBRID: "Hybrid",
    UNKNOWN: "Unknown",
  };
  return modes[mode] || mode;
};

const formatEmploymentType = (type: string) => {
  const types: Record<string, string> = {
    FULL_TIME: "Full-time",
    PART_TIME: "Part-time",
    CONTRACT: "Contract",
    INTERNSHIP: "Internship",
    UNKNOWN: "Unknown",
  };
  return types[type] || type;
};

const formatExperienceLevel = (level: string) => {
  const levels: Record<string, string> = {
    STUDENT: "Student",
    GRADUATE: "Graduate",
    JUNIOR: "Junior",
    MID: "Mid",
    SENIOR: "Senior",
    UNKNOWN: "Unknown",
  };
  return levels[level] || level;
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return null;
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export default function PublicOpportunityDetailPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const params = useParams();
  const opportunityId = Number(params?.id);

  useEffect(() => {
    if (!isLoading && isAuthenticated && Number.isFinite(opportunityId)) {
      window.location.href = `/dashboard/opportunities/${opportunityId}`;
    }
  }, [isAuthenticated, isLoading, opportunityId]);

  const { data: opportunity, isLoading: isLoadingOpportunity, error } = useQuery({
    queryKey: ["public-opportunity", opportunityId],
    queryFn: () => opportunitiesApi.getById(opportunityId),
    enabled: !isAuthenticated && !isLoading && Number.isFinite(opportunityId),
  });

  const applyUrl = opportunity?.source_url || null;

  const redirectToAuthFor = (intent: "apply" | "cover_letter" | "skill_gap") => {
    if (Number.isFinite(opportunityId)) {
      const next = `/dashboard/opportunities/${opportunityId}?intent=${encodeURIComponent(intent)}`;
      setPostAuthRedirect(next);
    }
    const hash = intent === "apply" ? "#login" : "#get-started";
    window.location.href = `/${hash}`;
  };

  const metaItems = useMemo(() => {
    if (!opportunity) return [];
    return [
      {
        label: "Location",
        value: opportunity.location?.name || "Not specified",
        icon: MapPin,
      },
      {
        label: "Posted",
        value: formatDate(opportunity.created_at) || "Recently",
        icon: Calendar,
      },
    ];
  }, [opportunity]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-20">
        <section className="container px-4 py-10">
          <FadeIn>
            <div className="mb-6">
              <Button asChild variant="ghost" className="gap-2">
                <Link href="/opportunities">
                  <ArrowLeft className="h-4 w-4" />
                  Back to opportunities
                </Link>
              </Button>
            </div>
          </FadeIn>

          {isLoadingOpportunity ? (
            <div className="text-sm text-muted-foreground">Loading...</div>
          ) : error || !opportunity ? (
            <FadeIn>
              <Card>
                <CardHeader>
                  <CardTitle>Opportunity not found</CardTitle>
                  <CardDescription>Please go back and try another opportunity.</CardDescription>
                </CardHeader>
              </Card>
            </FadeIn>
          ) : (
            <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
              <FadeIn>
                <Card className="overflow-hidden">
                  <CardHeader>
                    <CardTitle className="text-2xl leading-tight">{opportunity.title}</CardTitle>
                    <CardDescription className="text-base">{opportunity.organization}</CardDescription>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Badge variant="secondary">{formatWorkMode(opportunity.work_mode)}</Badge>
                      <Badge variant="outline">{formatEmploymentType(opportunity.employment_type)}</Badge>
                      <Badge variant="outline">{formatExperienceLevel(opportunity.experience_level)}</Badge>
                      {opportunity.is_remote && <Badge variant="default">Remote</Badge>}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid gap-4 sm:grid-cols-2">
                      {metaItems.map((item) => (
                        <div key={item.label} className="flex items-start gap-3 min-w-0">
                          <item.icon className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                          <div className="min-w-0">
                            <div className="text-xs text-muted-foreground">{item.label}</div>
                            <div className="text-sm font-medium truncate">{item.value}</div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div>
                      <div className="text-sm font-semibold mb-2">Description</div>
                      <div className="prose prose-sm max-w-none dark:prose-invert">
                        <div className="whitespace-pre-wrap break-words">
                          {opportunity.description_en || "No description provided."}
                        </div>
                      </div>
                    </div>

                    {applyUrl && (
                      <Button asChild className="gap-2 bg-[#0f9b57] hover:bg-[#0d8a4e] text-white">
                        <a href={applyUrl} target="_blank" rel="noreferrer">
                          Apply on source site
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </FadeIn>

              <FadeIn delay={0.05}>
                <Card className="border-border/60">
                  <CardHeader>
                    <CardTitle className="text-base">Unlock AI tools</CardTitle>
                    <CardDescription>
                      Sign in to generate a tailored cover letter and analyze skill gaps.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Button
                      variant="default"
                      className="gap-2 w-full"
                      onClick={() => redirectToAuthFor("cover_letter")}
                    >
                      <Lock className="h-4 w-4" />
                      <FileText className="h-4 w-4" />
                      Generate cover letter
                    </Button>
                    <Button
                      variant="outline"
                      className="gap-2 w-full"
                      onClick={() => redirectToAuthFor("skill_gap")}
                    >
                      <Lock className="h-4 w-4" />
                      <Target className="h-4 w-4" />
                      Skill-gap analysis
                    </Button>
                    <Button
                      variant="outline"
                      className="gap-2 w-full"
                      onClick={() => redirectToAuthFor("apply")}
                    >
                      <Lock className="h-4 w-4" />
                      <Sparkles className="h-4 w-4" />
                      Apply with AI help
                    </Button>

                    <Button asChild variant="secondary" className="w-full">
                      <Link href="/#login">Already have an account? Login</Link>
                    </Button>
                  </CardContent>
                </Card>
              </FadeIn>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
