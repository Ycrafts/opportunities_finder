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
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  Calendar,
  ExternalLink,
  FileText,
  Loader2,
  Lock,
  MapPin,
  Target,
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

const formatCompensation = (min: number | null, max: number | null) => {
  if (!min && !max) return null;
  if (min && max) return `ETB ${min.toLocaleString()} - ETB ${max.toLocaleString()}`;
  if (min) return `From ETB ${min.toLocaleString()}`;
  if (max) return `Up to ETB ${max.toLocaleString()}`;
  return null;
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

  const redirectToAuthFor = (intent: "apply" | "cover_letter" | "skill_gap") => {
    if (Number.isFinite(opportunityId)) {
      const next = `/dashboard/opportunities/${opportunityId}`;
      setPostAuthRedirect(next);
    }
    const hash = intent === "apply" ? "#login" : "#get-started";
    window.location.href = `/${hash}`;
  };

  if (isLoadingOpportunity) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 pt-20">
          <div className="container px-4 py-10">
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !opportunity) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 pt-20">
          <div className="container px-4 py-10">
            <Card>
              <CardHeader>
                <CardTitle>Opportunity not found</CardTitle>
                <CardDescription>
                  Please go back and try another opportunity.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  const compensation = formatCompensation(
    opportunity.min_compensation,
    opportunity.max_compensation
  );

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-20">
        <div className="container px-4 py-10">
          <div className="grid gap-6 lg:grid-cols-[1fr_22rem] lg:items-start">
            <FadeIn>
              <Card>
                <CardHeader className="space-y-5">
                  <Button
                    variant="ghost"
                    className="gap-2 px-0 text-muted-foreground hover:text-foreground w-fit"
                    asChild
                  >
                    <Link href="/opportunities">
                      <ArrowLeft className="h-4 w-4" />
                      Back to Opportunities
                    </Link>
                  </Button>
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-start gap-3">
                      <CardTitle className="text-2xl sm:text-3xl font-semibold flex-1">
                        {opportunity.title}
                      </CardTitle>
                      <Badge variant="secondary" className="text-xs h-fit">
                        {opportunity.op_type.name}
                      </Badge>
                    </div>
                    {opportunity.organization && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Building2 className="h-4 w-4" />
                        <span>{opportunity.organization}</span>
                      </div>
                    )}
                    <CardDescription className="text-sm">
                      {opportunity.domain.name}
                      {opportunity.specialization.name !== opportunity.domain.name &&
                        ` • ${opportunity.specialization.name}`}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex flex-wrap gap-3 text-sm">
                    {opportunity.is_remote ? (
                      <Badge variant="outline" className="gap-2">
                        <MapPin className="h-4 w-4" />
                        Remote
                      </Badge>
                    ) : opportunity.location ? (
                      <Badge variant="outline" className="gap-2">
                        <MapPin className="h-4 w-4" />
                        {opportunity.location.name}
                        {opportunity.location.parent &&
                          `, ${opportunity.location.parent.name}`}
                      </Badge>
                    ) : null}
                    {opportunity.work_mode !== "UNKNOWN" && (
                      <Badge variant="outline">
                        {formatWorkMode(opportunity.work_mode)}
                      </Badge>
                    )}
                    {opportunity.employment_type !== "UNKNOWN" && (
                      <Badge variant="outline">
                        {formatEmploymentType(opportunity.employment_type)}
                      </Badge>
                    )}
                    {opportunity.experience_level !== "UNKNOWN" && (
                      <Badge variant="outline">
                        {formatExperienceLevel(opportunity.experience_level)}
                      </Badge>
                    )}
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    {compensation && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground text-xs">ETB</span>
                        <span>{compensation.replace("ETB ", "")}</span>
                      </div>
                    )}
                    {opportunity.deadline && (
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>Deadline: {formatDate(opportunity.deadline)}</span>
                      </div>
                    )}
                  </div>

                  <div className="border-t pt-4">
                    <h3 className="text-sm font-semibold mb-2">Description</h3>
                    <p className="text-sm text-muted-foreground whitespace-pre-line">
                      {opportunity.description_en || "No description provided."}
                    </p>
                  </div>

                  {opportunity.op_type.name === "JOB" && (
                    <div className="border-t pt-4 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="text-xs font-semibold uppercase tracking-wide">
                          Skill gap analysis
                        </h3>
                        <Badge variant="outline" className="text-[10px] h-5">
                          Login required
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Sign in to generate a skill gap analysis for this opportunity.
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-fit gap-2"
                        onClick={() => redirectToAuthFor("skill_gap")}
                      >
                        <Lock className="h-4 w-4" />
                        Unlock analysis
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </FadeIn>

            <FadeIn delay={0.05}>
              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base">Actions</CardTitle>
                  <CardDescription>
                    Sign in to apply and unlock AI tools for this opportunity.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {opportunity.op_type.name === "JOB" && (
                    <Button
                      variant="default"
                      className="gap-2 w-full"
                      onClick={() => redirectToAuthFor("cover_letter")}
                    >
                      <Lock className="h-4 w-4" />
                      <FileText className="h-4 w-4" />
                      Generate Cover Letter
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    className="gap-2 w-full"
                    onClick={() => redirectToAuthFor("skill_gap")}
                  >
                    <Lock className="h-4 w-4" />
                    <Target className="h-4 w-4" />
                    Skill Gap Analysis
                  </Button>
                  {opportunity.source_url && (
                    <Button
                      variant="outline"
                      className="gap-2 w-full"
                      onClick={() => redirectToAuthFor("apply")}
                    >
                      <Lock className="h-4 w-4" />
                      Apply
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  )}

                  <Button asChild variant="secondary" className="w-full">
                    <Link href="/#login">Already have an account? Login</Link>
                  </Button>
                </CardContent>
              </Card>
            </FadeIn>
          </div>
        </div>
      </main>
    </div>
  );
}
