"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/contexts/auth-context";
import { opportunitiesApi } from "@/lib/api/opportunities";
import apiClient from "@/lib/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FadeIn } from "@/components/animations/fade-in";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Building2,
  Calendar,
  DollarSign,
  ExternalLink,
  Loader2,
  MapPin,
  Target,
  Briefcase,
  Users,
  FileText,
  Bell,
  Settings,
  Sliders,
  LayoutDashboard,
} from "lucide-react";

const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Opportunities", href: "/dashboard/opportunities", icon: Briefcase },
  { title: "Matches", href: "/dashboard/matches", icon: Target },
  { title: "Profile", href: "/dashboard/profile", icon: Users },
  { title: "Preferences", href: "/dashboard/preferences", icon: Sliders },
  {
    title: "Notifications",
    href: "/dashboard/notifications",
    icon: Bell,
    badge: 0,
  },
  { title: "Settings", href: "/dashboard/settings", icon: Settings },
];

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
  if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
  if (min) return `From $${min.toLocaleString()}`;
  if (max) return `Up to $${max.toLocaleString()}`;
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

export default function OpportunityDetailPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const opportunityId = Number(params?.id);
  const queryClient = useQueryClient();

  type CoverLetter = {
    id: number;
    opportunity: number;
    opportunity_id?: number;
    generated_content: string;
    edited_content: string;
    final_content: string;
    status: string;
    version: number;
    error_message: string;
  };

  const {
    data: opportunity,
    isLoading: isLoadingOpportunity,
    error,
  } = useQuery({
    queryKey: ["opportunity", opportunityId],
    queryFn: () => opportunitiesApi.getById(opportunityId),
    enabled: isAuthenticated && Number.isFinite(opportunityId),
  });

  const {
    data: coverLetters,
    isLoading: isLoadingCoverLetters,
  } = useQuery({
    queryKey: ["cover-letters"],
    queryFn: async () => {
      const response = await apiClient.get<{ results: CoverLetter[] }>(
        "/cover-letters/"
      );
      return response.data.results ?? [];
    },
    enabled: isAuthenticated,
  });

  const coverLetter = useMemo(() => {
    if (!coverLetters?.length || !Number.isFinite(opportunityId)) return null;
    const matches = coverLetters.filter(
      (letter) =>
        letter.opportunity === opportunityId ||
        letter.opportunity_id === opportunityId
    );
    if (!matches.length) return null;
    return matches.sort((a, b) => b.version - a.version)[0];
  }, [coverLetters, opportunityId]);

  const {
    data: coverLetterDetail,
    isLoading: isLoadingCoverLetterDetail,
  } = useQuery({
    queryKey: ["cover-letter", coverLetter?.id],
    queryFn: async () => {
      if (!coverLetter) return null;
      const response = await apiClient.get<CoverLetter>(
        `/cover-letters/${coverLetter.id}/`
      );
      return response.data;
    },
    enabled: Boolean(coverLetter?.id),
    refetchInterval: coverLetter?.status === "GENERATING" ? 4000 : false,
  });

  const [coverLetterDraft, setCoverLetterDraft] = useState("");
  const [hasEditedDraft, setHasEditedDraft] = useState(false);

  useEffect(() => {
    if (!coverLetterDetail) return;
    if (hasEditedDraft) return;
    setCoverLetterDraft(coverLetterDetail.final_content || "");
  }, [coverLetterDetail, hasEditedDraft]);

  const generateCoverLetterMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/cover-letters/generate/", {
        opportunity_id: opportunityId,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success("Cover letter generation started.");
      queryClient.invalidateQueries({ queryKey: ["cover-letters"] });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to generate cover letter.";
      toast.error(message);
    },
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  const updateCoverLetterMutation = useMutation({
    mutationFn: async (updatedContent: string) => {
      if (!coverLetter) {
        throw new Error("No cover letter available to update.");
      }
      const response = await apiClient.patch(`/cover-letters/${coverLetter.id}/`, {
        edited_content: updatedContent,
      });
      return response.data as CoverLetter;
    },
    onSuccess: () => {
      toast.success("Cover letter saved.");
      setHasEditedDraft(false);
      queryClient.invalidateQueries({ queryKey: ["cover-letters"] });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to save cover letter.";
      toast.error(message);
    },
  });


  if (isLoading || isLoadingOpportunity) {
    return (
      <DashboardLayout navItems={navItems} title="Opportunity Details">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </DashboardLayout>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (error || !opportunity) {
    return (
      <DashboardLayout navItems={navItems} title="Opportunity Details">
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">Failed to load opportunity details.</p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  const compensation = formatCompensation(
    opportunity.min_compensation,
    opportunity.max_compensation
  );

  return (
    <DashboardLayout navItems={navItems} title="Opportunity Details">
      <div className="space-y-6 max-w-5xl">
        <FadeIn>
          <Card>
            <CardHeader className="space-y-5">
              <Button
                variant="ghost"
                className="gap-2 px-0 text-muted-foreground hover:text-foreground w-fit"
                onClick={() => router.back()}
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Opportunities
              </Button>
              <div className="grid gap-6 md:grid-cols-[1fr_auto] md:items-start">
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
                <div className="flex flex-col gap-2 w-full md:w-56">
                  {opportunity.op_type.name === "JOB" && (
                    <Button
                      variant="default"
                      className="gap-2 w-full"
                      disabled={generateCoverLetterMutation.isPending}
                      onClick={() => generateCoverLetterMutation.mutate()}
                    >
                      {generateCoverLetterMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <FileText className="h-4 w-4" />
                      )}
                      Generate Cover Letter
                    </Button>
                  )}
                  {opportunity.source_url && (
                    <Button asChild variant="outline" className="gap-2 w-full">
                      <a
                        href={opportunity.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Apply
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                </div>
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
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span>{compensation}</span>
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
                    <h3 className="text-sm font-semibold">Cover Letter</h3>
                    {coverLetterDetail?.status && (
                      <Badge variant="outline" className="text-xs">
                        {coverLetterDetail.status}
                      </Badge>
                    )}
                  </div>
                  {isLoadingCoverLetters || isLoadingCoverLetterDetail ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading cover letter...
                    </div>
                  ) : coverLetterDetail ? (
                    <div className="space-y-3">
                      {coverLetterDetail.status === "GENERATING" && (
                        <p className="text-sm text-muted-foreground">
                          Generating your cover letter. It will appear here automatically.
                        </p>
                      )}
                      <Textarea
                        value={coverLetterDraft}
                        onChange={(event) => {
                          setCoverLetterDraft(event.target.value);
                          setHasEditedDraft(true);
                        }}
                        placeholder="Your cover letter will appear here."
                        className="min-h-[220px] text-sm"
                      />
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="default"
                          className="gap-2"
                          disabled={
                            updateCoverLetterMutation.isPending ||
                            !hasEditedDraft ||
                            !coverLetterDraft.trim()
                          }
                          onClick={() =>
                            updateCoverLetterMutation.mutate(coverLetterDraft)
                          }
                        >
                          {updateCoverLetterMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : null}
                          Save edits
                        </Button>
                        <Button
                          variant="outline"
                          disabled={updateCoverLetterMutation.isPending}
                          onClick={() => {
                            setCoverLetterDraft(coverLetterDetail.final_content || "");
                            setHasEditedDraft(false);
                          }}
                        >
                          Reset
                        </Button>
                      </div>
                      {coverLetterDetail.status === "FAILED" &&
                        coverLetterDetail.error_message && (
                        <p className="text-sm text-destructive">
                          {coverLetterDetail.error_message}
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No cover letter yet. Generate one to start editing.
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </DashboardLayout>
  );
}
