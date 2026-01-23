"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  Bell,
  Settings,
  Target,
  Search,
  MapPin,
  Calendar,
  DollarSign,
  Building2,
  Filter,
  X,
  Sliders,
} from "lucide-react";
import { FadeIn } from "@/components/animations/fade-in";
import { useAuth } from "@/contexts/auth-context";
import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { useInfiniteQuery } from "@tanstack/react-query";
import { opportunitiesApi, type Opportunity } from "@/lib/api/opportunities";

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

export default function OpportunitiesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<{
    is_remote: boolean | null;
    work_mode: string | null;
    experience_level: string | null;
    status: string | null;
  }>({
    is_remote: null,
    work_mode: null,
    experience_level: null,
    status: null,
  });
  const observerTarget = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch opportunities using infinite query
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isLoadingOpportunities,
    error,
  } = useInfiniteQuery({
    queryKey: [
      "opportunities",
      searchQuery,
      filters.is_remote,
      filters.work_mode,
      filters.experience_level,
      filters.status,
    ],
    queryFn: ({ pageParam = 1 }) =>
      opportunitiesApi.list({
        q: searchQuery || undefined,
        is_remote: filters.is_remote !== null ? filters.is_remote : undefined,
        work_mode: filters.work_mode || undefined,
        experience_level: filters.experience_level || undefined,
        status: filters.status || undefined,
        page: pageParam,
      }),
    getNextPageParam: (lastPage) => {
      if (lastPage.next) {
        // Extract page number from next URL
        const url = new URL(lastPage.next);
        const page = url.searchParams.get("page");
        return page ? parseInt(page, 10) : undefined;
      }
      return undefined;
    },
    initialPageParam: 1,
    enabled: isAuthenticated,
  });

  // Flatten all pages into a single array (dedupe by id)
  const opportunities = useMemo(() => {
    const items = data?.pages.flatMap((page) => page.results) || [];
    const seen = new Set<number>();
    return items.filter((item) => {
      if (seen.has(item.id)) {
        return false;
      }
      seen.add(item.id);
      return true;
    });
  }, [data]);
  const totalCount = data?.pages[0]?.count || 0;

  // Intersection Observer for infinite scroll
  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      if (target.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [hasNextPage, isFetchingNextPage, fetchNextPage]
  );

  useEffect(() => {
    const element = observerTarget.current;
    if (!element) return;

    const observer = new IntersectionObserver(handleObserver, {
      threshold: 0.1,
    });
    observer.observe(element);

    return () => {
      if (element) {
        observer.unobserve(element);
      }
    };
  }, [handleObserver]);

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
    if (min && max)
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
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

  const getDaysUntilDeadline = (dateString: string | null) => {
    if (!dateString) return null;
    const deadline = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadline.setHours(0, 0, 0, 0);
    const diff = Math.ceil(
      (deadline.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );
    return diff;
  };

  return (
    <DashboardLayout navItems={navItems} title="Opportunities">
      <div className="space-y-6">
        {/* Header */}
        <FadeIn>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight">
                Opportunities
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Browse and discover opportunities that match your interests
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="gap-2 w-full sm:w-auto"
            >
              <Filter className="h-4 w-4" />
              Filters
            </Button>
          </div>
        </FadeIn>

        {/* Search Bar */}
        <FadeIn delay={0.1}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search opportunities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-11"
            />
          </div>
        </FadeIn>

        {/* Filters (Collapsible) */}
        {showFilters && (
          <FadeIn delay={0.2}>
            <Card className="border-border/60">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-semibold">
                    Filters
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowFilters(false)}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 sm:grid sm:grid-cols-2 sm:gap-6 lg:grid-cols-3 sm:space-y-0">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                    <label className="text-sm font-semibold text-foreground whitespace-nowrap shrink-0">
                      Work Mode
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        variant={
                          filters.is_remote === true ? "default" : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            is_remote: prev.is_remote === true ? null : true,
                            work_mode: null,
                          }))
                        }
                      >
                        Remote
                      </Badge>
                      <Badge
                        variant={
                          filters.is_remote === false ? "default" : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            is_remote: prev.is_remote === false ? null : false,
                            work_mode: null,
                          }))
                        }
                      >
                        Onsite
                      </Badge>
                      <Badge
                        variant={
                          filters.work_mode === "HYBRID" ? "default" : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            work_mode:
                              prev.work_mode === "HYBRID" ? null : "HYBRID",
                            is_remote: null,
                          }))
                        }
                      >
                        Hybrid
                      </Badge>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                    <label className="text-sm font-semibold text-foreground whitespace-nowrap shrink-0">
                      Status
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        variant={
                          filters.status === "ACTIVE" ? "default" : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            status: prev.status === "ACTIVE" ? null : "ACTIVE",
                          }))
                        }
                      >
                        Active
                      </Badge>
                      <Badge
                        variant={
                          filters.status === "EXPIRED" ? "default" : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            status: prev.status === "EXPIRED" ? null : "EXPIRED",
                          }))
                        }
                      >
                        Expired
                      </Badge>
                      <Badge
                        variant={
                          filters.status === "ARCHIVED"
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            status:
                              prev.status === "ARCHIVED" ? null : "ARCHIVED",
                          }))
                        }
                      >
                        Archived
                      </Badge>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                    <label className="text-sm font-semibold text-foreground whitespace-nowrap shrink-0">
                      Experience Level
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        variant={
                          filters.experience_level === "JUNIOR"
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            experience_level:
                              prev.experience_level === "JUNIOR"
                                ? null
                                : "JUNIOR",
                          }))
                        }
                      >
                        Junior
                      </Badge>
                      <Badge
                        variant={
                          filters.experience_level === "MID"
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            experience_level:
                              prev.experience_level === "MID" ? null : "MID",
                          }))
                        }
                      >
                        Mid
                      </Badge>
                      <Badge
                        variant={
                          filters.experience_level === "SENIOR"
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer hover:bg-muted"
                        onClick={() =>
                          setFilters((prev) => ({
                            ...prev,
                            experience_level:
                              prev.experience_level === "SENIOR"
                                ? null
                                : "SENIOR",
                          }))
                        }
                      >
                        Senior
                      </Badge>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4 sm:col-span-2 lg:col-span-1">
                    <label className="text-sm font-semibold text-foreground whitespace-nowrap shrink-0">
                      Clear Filters
                    </label>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setFilters({
                          is_remote: null,
                          work_mode: null,
                          experience_level: null,
                          status: null,
                        })
                      }
                      className="h-7 px-3 text-xs w-full sm:w-auto"
                    >
                      Reset All
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </FadeIn>
        )}

        {/* Opportunities Grid */}
        {isLoadingOpportunities ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-muted-foreground">
              Loading opportunities...
            </div>
          </div>
        ) : error ? (
          <Card className="border-border/60">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-4 rounded-full bg-destructive/10 p-3">
                <Briefcase className="h-6 w-6 text-destructive" />
              </div>
              <p className="text-sm font-medium text-foreground mb-1">
                Failed to load opportunities
              </p>
              <p className="text-xs font-normal text-muted-foreground">
                Please try refreshing the page
              </p>
            </CardContent>
          </Card>
        ) : opportunities.length === 0 ? (
          <Card className="border-border/60">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-4 rounded-full bg-muted/50 p-3">
                <Briefcase className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm font-normal text-muted-foreground">
                No opportunities found. Try adjusting your search or filters.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {opportunities.map((opportunity, index) => {
              const daysUntilDeadline = getDaysUntilDeadline(
                opportunity.deadline
              );
              const compensation = formatCompensation(
                opportunity.min_compensation,
                opportunity.max_compensation
              );

              return (
                <FadeIn key={opportunity.id} delay={0.1 * (index % 6)}>
                  <Card className="border-border/60 hover:border-border transition-all cursor-pointer group h-full flex flex-col">
                    <Link href={`/dashboard/opportunities/${opportunity.id}`}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex-1 min-w-0">
                            <CardTitle className="text-base font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                              {opportunity.title}
                            </CardTitle>
                            {opportunity.organization && (
                              <div className="flex items-center gap-1.5 mt-1.5">
                                <Building2 className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                                <span className="text-xs text-muted-foreground truncate">
                                  {opportunity.organization}
                                </span>
                              </div>
                            )}
                          </div>
                          <Badge
                            variant="secondary"
                            className="flex-shrink-0 text-xs"
                          >
                            {opportunity.op_type.name}
                          </Badge>
                        </div>
                        <CardDescription className="text-xs line-clamp-2">
                          {opportunity.description_en ||
                            "No description available"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0 flex-1 flex flex-col">
                        <div className="space-y-2 flex-1">
                          {/* Location & Work Mode */}
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            {opportunity.is_remote ? (
                              <>
                                <MapPin className="h-3.5 w-3.5 flex-shrink-0" />
                                <span>Remote</span>
                              </>
                            ) : opportunity.location ? (
                              <>
                                <MapPin className="h-3.5 w-3.5 flex-shrink-0" />
                                <span className="truncate">
                                  {opportunity.location.name}
                                  {opportunity.location.parent &&
                                    `, ${opportunity.location.parent.name}`}
                                </span>
                              </>
                            ) : null}
                            {!opportunity.is_remote &&
                              opportunity.work_mode !== "UNKNOWN" && (
                                <span className="text-muted-foreground/60">
                                  •
                                </span>
                              )}
                            {opportunity.work_mode !== "UNKNOWN" &&
                              !opportunity.is_remote && (
                                <span>
                                  {formatWorkMode(opportunity.work_mode)}
                                </span>
                              )}
                          </div>

                          {/* Employment Type & Experience */}
                          <div className="flex items-center gap-2 flex-wrap">
                            {opportunity.employment_type !== "UNKNOWN" && (
                              <Badge variant="outline" className="text-xs">
                                {formatEmploymentType(
                                  opportunity.employment_type
                                )}
                              </Badge>
                            )}
                            {opportunity.experience_level !== "UNKNOWN" && (
                              <Badge variant="outline" className="text-xs">
                                {formatExperienceLevel(
                                  opportunity.experience_level
                                )}
                              </Badge>
                            )}
                          </div>

                          {/* Compensation */}
                          {compensation && (
                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                              <DollarSign className="h-3.5 w-3.5 flex-shrink-0" />
                              <span>{compensation}</span>
                            </div>
                          )}

                          {/* Deadline */}
                          {opportunity.deadline && (
                            <div className="flex items-center gap-1.5 text-xs">
                              <Calendar className="h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                              <span className="text-muted-foreground">
                                Deadline: {formatDate(opportunity.deadline)}
                              </span>
                              {daysUntilDeadline !== null && (
                                <>
                                  {daysUntilDeadline < 0 ? (
                                    <Badge
                                      variant="destructive"
                                      className="text-xs ml-auto"
                                    >
                                      Expired
                                    </Badge>
                                  ) : daysUntilDeadline <= 7 ? (
                                    <Badge
                                      variant="destructive"
                                      className="text-xs ml-auto"
                                    >
                                      {daysUntilDeadline}d left
                                    </Badge>
                                  ) : daysUntilDeadline <= 30 ? (
                                    <Badge
                                      variant="secondary"
                                      className="text-xs ml-auto"
                                    >
                                      {daysUntilDeadline}d left
                                    </Badge>
                                  ) : null}
                                </>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Domain & Specialization */}
                        <div className="mt-3 pt-3 border-t border-border/60">
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="truncate">
                              {opportunity.domain.name}
                              {opportunity.specialization.name !==
                                opportunity.domain.name &&
                                ` • ${opportunity.specialization.name}`}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Link>
                  </Card>
                </FadeIn>
              );
            })}
          </div>
        )}

        {/* Infinite scroll trigger and loading indicator */}
        {opportunities.length > 0 && (
          <>
            <div ref={observerTarget} className="h-4" />
            {isFetchingNextPage && (
              <div className="flex items-center justify-center py-8">
                <div className="text-sm text-muted-foreground">
                  Loading more opportunities...
                </div>
              </div>
            )}
            {!hasNextPage && opportunities.length > 0 && (
              <div className="flex items-center justify-center py-8 border-t border-border/60">
                <div className="text-sm text-muted-foreground">
                  You've reached the end. Showing all {totalCount}{" "}
                  opportunities.
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
