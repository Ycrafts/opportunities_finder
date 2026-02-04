"use client";

import { Header } from "@/components/layout/header";
import { FadeIn } from "@/components/animations/fade-in";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { opportunitiesApi, type Opportunity } from "@/lib/api/opportunities";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/auth-context";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Filter, MapPin, Search, X } from "lucide-react";

export default function PublicOpportunitiesPage() {
  const { isAuthenticated, isLoading } = useAuth();
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

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      window.location.href = "/dashboard/opportunities";
    }
  }, [isAuthenticated, isLoading]);

  const observerTarget = useRef<HTMLDivElement>(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isLoadingOpportunities,
    error,
  } = useInfiniteQuery({
    queryKey: [
      "public-opportunities",
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
        const url = new URL(lastPage.next);
        const page = url.searchParams.get("page");
        return page ? parseInt(page, 10) : undefined;
      }
      return undefined;
    },
    initialPageParam: 1,
    enabled: !isAuthenticated && !isLoading,
  });

  const opportunities = useMemo(() => {
    const items = data?.pages.flatMap((page) => page.results) || [];
    const seen = new Set<number>();
    const deduped = items.filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
    return [...deduped].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [data]);

  const totalCount = data?.pages[0]?.count || 0;

  const formatWorkMode = (mode: string) => {
    const modes: Record<string, string> = {
      REMOTE: "Remote",
      ONSITE: "Onsite",
      HYBRID: "Hybrid",
      UNKNOWN: "Unknown",
    };
    return modes[mode] || mode;
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
      observer.disconnect();
    };
  }, [handleObserver]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-20">
        <section className="border-b bg-muted/20">
          <div className="container px-4 py-10">
            <FadeIn>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Opportunities</h1>
                  <p className="text-sm text-muted-foreground">
                    Browse real opportunities. Sign in to unlock AI tools like cover letters and skill-gap analysis.
                  </p>
                </div>
                <Button
                  variant="default"
                  onClick={() => setShowFilters(!showFilters)}
                  className="gap-2 w-full sm:w-auto bg-[#0f9b57] hover:bg-[#0d8a4e] text-white"
                >
                  <Filter className="h-4 w-4" />
                  Filters
                </Button>
              </div>
            </FadeIn>

            <FadeIn delay={0.1}>
              <div className="mt-6 relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search opportunities..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-11"
                />
              </div>
            </FadeIn>

            {showFilters && (
              <FadeIn delay={0.2}>
                <Card className="mt-6 border-border/60">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-semibold">Filters</CardTitle>
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
                            variant={filters.is_remote === true ? "default" : "outline"}
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
                            variant={filters.is_remote === false ? "default" : "outline"}
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
                            variant={filters.work_mode === "HYBRID" ? "default" : "outline"}
                            className="cursor-pointer hover:bg-muted"
                            onClick={() =>
                              setFilters((prev) => ({
                                ...prev,
                                work_mode: prev.work_mode === "HYBRID" ? null : "HYBRID",
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
                          Experience
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {(["STUDENT", "GRADUATE", "JUNIOR", "MID", "SENIOR"] as const).map((lvl) => (
                            <Badge
                              key={lvl}
                              variant={filters.experience_level === lvl ? "default" : "outline"}
                              className="cursor-pointer hover:bg-muted"
                              onClick={() =>
                                setFilters((prev) => ({
                                  ...prev,
                                  experience_level: prev.experience_level === lvl ? null : lvl,
                                }))
                              }
                            >
                              {formatExperienceLevel(lvl)}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                        <label className="text-sm font-semibold text-foreground whitespace-nowrap shrink-0">
                          Status
                        </label>
                        <div className="flex flex-wrap gap-2">
                          <Badge
                            variant={filters.status === "ACTIVE" ? "default" : "outline"}
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
                            variant={filters.status === "EXPIRED" ? "default" : "outline"}
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
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </FadeIn>
            )}
          </div>
        </section>

        <section className="container px-4 py-10">
          <FadeIn>
            <div className="mb-6 flex items-center justify-between gap-4">
              <div className="text-sm text-muted-foreground">
                {isLoadingOpportunities ? "Loading..." : `${totalCount.toLocaleString()} results`}
              </div>
              <Button asChild variant="outline" className="border-white/20">
                <Link href="/#login">Sign in to unlock AI tools</Link>
              </Button>
            </div>
          </FadeIn>

          {error ? (
            <FadeIn>
              <Card>
                <CardHeader>
                  <CardTitle>Couldn’t load opportunities</CardTitle>
                  <CardDescription>
                    Please try again in a moment.
                  </CardDescription>
                </CardHeader>
              </Card>
            </FadeIn>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {opportunities.map((opportunity: Opportunity, idx: number) => (
                <FadeIn key={opportunity.id} delay={Math.min(0.05 * idx, 0.25)}>
                  <Link href={`/opportunities/${opportunity.id}`} className="block h-full">
                    <Card className="h-full transition-all hover:shadow-lg hover:border-border/80 overflow-hidden">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg leading-tight overflow-hidden text-ellipsis line-clamp-2">
                          {opportunity.title}
                        </CardTitle>
                        <CardDescription className="overflow-hidden text-ellipsis whitespace-nowrap">
                          {opportunity.organization}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="secondary">{formatWorkMode(opportunity.work_mode)}</Badge>
                          <Badge variant="outline">{formatExperienceLevel(opportunity.experience_level)}</Badge>
                          {opportunity.is_remote && <Badge variant="default">Remote</Badge>}
                        </div>

                        <div className="flex items-center gap-2 text-sm text-muted-foreground min-w-0">
                          <MapPin className="h-4 w-4 shrink-0" />
                          <span className="truncate min-w-0">
                            {opportunity.location?.name || "Location not specified"}
                          </span>
                        </div>

                        <div className="text-xs text-muted-foreground">
                          Posted {formatDate(opportunity.created_at) || "Recently"}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </FadeIn>
              ))}
            </div>
          )}

          <div ref={observerTarget} className="h-8" />

          {isFetchingNextPage && (
            <div className="mt-8 text-center text-sm text-muted-foreground">Loading more...</div>
          )}

          {!hasNextPage && opportunities.length > 0 && (
            <div className="mt-10 text-center text-sm text-muted-foreground">You’ve reached the end.</div>
          )}

          {!isLoadingOpportunities && opportunities.length === 0 && !error && (
            <FadeIn>
              <Card>
                <CardHeader>
                  <CardTitle>No results</CardTitle>
                  <CardDescription>Try adjusting your search or filters.</CardDescription>
                </CardHeader>
              </Card>
            </FadeIn>
          )}
        </section>
      </main>
    </div>
  );
}
