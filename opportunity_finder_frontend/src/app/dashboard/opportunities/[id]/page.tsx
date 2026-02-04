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
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Award,
  Briefcase,
  Building2,
  Calendar,
  CheckCircle2,
  ExternalLink,
  FileText,
  Globe,
  LayoutDashboard,
  MapPin,
  Loader2,
  Share2,
  Sparkles,
  Target,
  Users,
  Bell,
  Settings,
  Sliders,
  Crown,
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
  { title: "Upgrade", href: "/dashboard/upgrade", icon: Crown },
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

export default function OpportunityDetailPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
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

  type SkillGapAnalysis = {
    id: number;
    opportunity: number;
    opportunity_title?: string;
    opportunity_organization?: string;
    status: string;
    missing_skills: string[];
    skill_gaps: Record<
      string,
      {
        current_level: string;
        required_level: string;
        gap_size: string;
        priority?: string;
      }
    >;
    recommended_actions: Array<{
      skill?: string;
      action_type?: string;
      description?: string;
      resource?: string;
      estimated_time_weeks?: number;
      cost?: string;
      priority?: string;
    }>;
    alternative_suggestions: Record<string, any>;
    confidence_score: number | null;
    estimated_time_months: number | null;
    error_message: string;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
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

  const [coverLetterDraft, setCoverLetterDraft] = useState("");
  const [hasEditedDraft, setHasEditedDraft] = useState(false);
  const [skillGapAnalysisId, setSkillGapAnalysisId] = useState<number | null>(null);

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
    data: skillGapAnalyses,
    isLoading: isLoadingSkillGapAnalyses,
  } = useQuery({
    queryKey: ["skill-gap-analyses"],
    queryFn: async () => {
      const response = await apiClient.get<{ results: SkillGapAnalysis[] }>(
        "/skill-gap-analysis/"
      );
      return response.data.results ?? [];
    },
    enabled: isAuthenticated,
  });

  const skillGapAnalysis = useMemo(() => {
    if (!skillGapAnalyses?.length || !Number.isFinite(opportunityId)) return null;
    const matches = skillGapAnalyses.filter(
      (analysis) => analysis.opportunity === opportunityId
    );
    if (!matches.length) return null;
    return matches.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0];
  }, [skillGapAnalyses, opportunityId]);

  const activeSkillGapAnalysisId =
    skillGapAnalysisId ?? skillGapAnalysis?.id ?? null;

  const {
    data: skillGapAnalysisDetail,
    isLoading: isLoadingSkillGapAnalysisDetail,
  } = useQuery<SkillGapAnalysis | null>({
    queryKey: ["skill-gap-analysis", activeSkillGapAnalysisId],
    queryFn: async () => {
      if (!activeSkillGapAnalysisId) return null;
      const response = await apiClient.get<SkillGapAnalysis>(
        `/skill-gap-analysis/${activeSkillGapAnalysisId}/`
      );
      return response.data;
    },
    enabled: Boolean(activeSkillGapAnalysisId),
    refetchInterval: (query) =>
      query.state.data?.status === "GENERATING" ? 4000 : false,
  });

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
      const code = error?.response?.data?.code;
      const upgradeUrl = error?.response?.data?.upgrade_url;
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to generate cover letter.";
      toast.error(message);
      if (code === "premium_required" && upgradeUrl) {
        router.push(upgradeUrl);
      }
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

  const analyzeSkillGapMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/skill-gap-analysis/analyze/", {
        opportunity_id: opportunityId,
      });
      return response.data;
    },
    onSuccess: (data: SkillGapAnalysis) => {
      if (data?.id) {
        setSkillGapAnalysisId(data.id);
      }
      toast.success("Skill gap analysis started.");
      queryClient.invalidateQueries({ queryKey: ["skill-gap-analyses"] });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to start skill gap analysis.";
      toast.error(message);
    },
  });

  useEffect(() => {
    if (!isAuthenticated || isLoading) return;
    if (!Number.isFinite(opportunityId)) return;
    if (!opportunity) return;

    const intent = searchParams?.get("intent");
    if (!intent) return;

    if (intent === "cover_letter") {
      if (!generateCoverLetterMutation.isPending) {
        generateCoverLetterMutation.mutate();
      }
    } else if (intent === "skill_gap") {
      if (!analyzeSkillGapMutation.isPending) {
        analyzeSkillGapMutation.mutate();
      }
    } else if (intent === "apply") {
      if (opportunity.source_url) {
        window.open(opportunity.source_url, "_blank", "noopener,noreferrer");
      }
    }

    const next = new URL(window.location.href);
    next.searchParams.delete("intent");
    router.replace(next.pathname + next.search);
  }, [
    analyzeSkillGapMutation,
    generateCoverLetterMutation,
    isAuthenticated,
    isLoading,
    opportunity,
    opportunityId,
    router,
    searchParams,
  ]);


  if (isLoading || isLoadingOpportunity) {
    return (
      <DashboardLayout navItems={navItems}>
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
      <DashboardLayout navItems={navItems}>
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
    <DashboardLayout navItems={navItems}>
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
                  <Button
                    variant="outline"
                    className="gap-2 w-full"
                    disabled={analyzeSkillGapMutation.isPending}
                    onClick={() => analyzeSkillGapMutation.mutate()}
                  >
                    {analyzeSkillGapMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Target className="h-4 w-4" />
                    )}
                    Skill Gap Analysis
                  </Button>
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
                    {skillGapAnalysisDetail?.status && (
                      <Badge variant="outline" className="text-[10px] h-5">
                        {skillGapAnalysisDetail.status}
                      </Badge>
                    )}
                  </div>
                  {isLoadingSkillGapAnalyses ||
                  isLoadingSkillGapAnalysisDetail ||
                  skillGapAnalysisDetail?.status === "GENERATING" ? (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating skill gap analysis...
                    </div>
                  ) : skillGapAnalysisDetail ? (
                    <div className="space-y-3 text-xs">
                      {skillGapAnalysisDetail.error_message && (
                        <p className="text-destructive text-xs">
                          {skillGapAnalysisDetail.error_message}
                        </p>
                      )}
                      {skillGapAnalysisDetail.alternative_suggestions?.summary && (
                        <p className="text-muted-foreground text-xs">
                          {skillGapAnalysisDetail.alternative_suggestions.summary}
                        </p>
                      )}
                      {skillGapAnalysisDetail.missing_skills?.length > 0 && (
                        <div>
                          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                            Missing skills
                          </p>
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {skillGapAnalysisDetail.missing_skills.map((skill) => (
                              <Badge key={skill} variant="secondary" className="text-[10px]">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {skillGapAnalysisDetail.skill_gaps &&
                      Object.keys(skillGapAnalysisDetail.skill_gaps).length > 0 ? (
                        <div>
                          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                            Skill gaps
                          </p>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2">
                            {Object.entries(skillGapAnalysisDetail.skill_gaps).map(
                              ([skill, gap]) => (
                                <div
                                  key={skill}
                                  className="flex flex-col gap-1 rounded-md border px-2.5 py-2"
                                >
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <span className="font-medium text-xs">{skill}</span>
                                    <Badge variant="outline" className="text-[10px] h-5">
                                      {gap.gap_size} gap
                                    </Badge>
                                  </div>
                                  <p className="text-[11px] text-muted-foreground">
                                    Current: {gap.current_level} • Required: {gap.required_level}
                                  </p>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      ) : null}
                      {skillGapAnalysisDetail.recommended_actions?.length > 0 && (
                        <div>
                          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                            Recommended actions
                          </p>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2">
                            {skillGapAnalysisDetail.recommended_actions.map((action, index) => (
                              <div
                                key={`${action.skill ?? "action"}-${index}`}
                                className="rounded-md border px-2.5 py-2"
                              >
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                  <span className="font-medium text-xs">
                                    {action.skill || "Recommendation"}
                                  </span>
                                  {action.action_type && (
                                    <Badge variant="outline" className="text-[10px] h-5">
                                      {action.action_type}
                                    </Badge>
                                  )}
                                </div>
                                {action.description && (
                                  <p className="text-[11px] text-muted-foreground mt-1">
                                    {action.description}
                                  </p>
                                )}
                                {action.resource && (
                                  <p className="text-[11px] text-muted-foreground">
                                    Resource: {action.resource}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      No analysis yet. Run a skill gap analysis to see recommendations.
                    </p>
                  )}
                </div>
              )}
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
