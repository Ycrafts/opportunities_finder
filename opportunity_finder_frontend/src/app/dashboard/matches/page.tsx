"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useInfiniteQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Briefcase,
  Target,
  Users,
  Sliders,
  Bell,
  Settings,
  FileText,
  MapPin,
  Calendar,
  Sparkles,
  Search,
  Crown,
} from "lucide-react";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { matchesApi, type MatchListItem, type MatchStatus } from "@/lib/api/matches";
import { useAuth } from "@/contexts/auth-context";
import { FadeIn } from "@/components/animations/fade-in";
import { cn } from "@/lib/utils";

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

const statusFilters: { label: string; value: MatchStatus | "ALL" }[] = [
  { label: "All", value: "ALL" },
  { label: "Active", value: "ACTIVE" },
  { label: "Expired", value: "EXPIRED" },
];

const formatDate = (value: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const similarityLabel = (score: number) => {
  if (score >= 8) {
    return "Strong alignment";
  }
  if (score >= 7) {
    return "Good alignment";
  }
  if (score >= 3) {
    return "Potential fit";
  }
  return "Low alignment";
};

const similarityTone = (score: number) => {
  if (score >= 8) return "bg-foreground text-background";
  if (score >= 7) return "bg-muted text-foreground";
  if (score >= 3) return "bg-muted/60 text-foreground";
  return "bg-muted/40 text-muted-foreground";
};

export default function MatchesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<MatchStatus | "ALL">("ALL");
  const [query, setQuery] = useState("");
  const observerTarget = useRef<HTMLDivElement>(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isLoadingMatches,
    error,
  } = useInfiniteQuery({
    queryKey: ["matches", statusFilter],
    queryFn: ({ pageParam = 1 }) =>
      matchesApi.listPaginated({
        status: statusFilter === "ALL" ? undefined : statusFilter,
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
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  const matches = useMemo(() => {
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

  const filteredMatches = useMemo(() => {
    if (!matches.length) return [];
    if (!query.trim()) return matches;
    const lowered = query.toLowerCase();
    return matches.filter((match) => {
      const opp = match.opportunity;
      return [opp.title, opp.organization, opp.domain, opp.specialization, opp.location]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(lowered));
    });
  }, [matches, query]);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      if (target.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage]
  );

  useEffect(() => {
    const element = observerTarget.current;
    if (!element) return;

    const observer = new IntersectionObserver(handleObserver, { threshold: 0.1 });
    observer.observe(element);

    return () => {
      if (element) observer.unobserve(element);
    };
  }, [handleObserver]);

  return (
    <DashboardLayout navItems={navItems}>
      <div className="space-y-6 max-w-6xl">
        <FadeIn>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <h2 className="text-2xl font-semibold">Your matches</h2>
              <p className="text-sm text-muted-foreground">
                Curated opportunities scored against your profile and preferences.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search matches"
                  className="pl-9 w-60"
                />
              </div>
              <Button 
              asChild variant="default"
              className="bg-[#0f9b57] hover:bg-[#0d8a4e] text-white">
                <Link href="/dashboard/preferences">Refine preferences</Link>
              </Button>
            </div>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <Card>
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-base">Match overview</CardTitle>
              <div className="flex flex-wrap gap-2">
                {statusFilters.map((filter) => (
                  <Button
                    key={filter.value}
                    variant={statusFilter === filter.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setStatusFilter(filter.value)}
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoadingMatches ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Sparkles className="h-4 w-4 animate-pulse" />
                  Loading matches...
                </div>
              ) : error ? (
                <p className="text-sm text-destructive">Failed to load matches.</p>
              ) : filteredMatches.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border/60 px-6 py-10 text-center">
                  <p className="text-sm font-medium">No matches yet</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Update your preferences or wait for new opportunities.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredMatches.map((match: MatchListItem) => (
                    <Card
                      key={match.id}
                      className="border-border/60 transition-shadow hover:shadow-sm"
                    >
                      <CardContent className="p-0">
                        <Link
                          href={`/dashboard/opportunities/${match.opportunity.id}`}
                          className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="space-y-2">
                            <div className="flex items-start gap-3">
                              <div className="space-y-1">
                                <h3 className="text-base font-semibold">
                                  {match.opportunity.title}
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                  {match.opportunity.organization || "Organization unknown"}
                                </p>
                              </div>
                              <Badge
                                className={cn(
                                  "text-xs leading-none px-2.5 py-1 translate-y-[2px]",
                                  similarityTone(match.match_score)
                                )}
                              >
                                {similarityLabel(match.match_score)}
                              </Badge>
                            </div>
                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                              <Badge variant="outline">{match.opportunity.op_type}</Badge>
                              <span className="inline-flex items-center gap-1">
                                <MapPin className="h-3.5 w-3.5" />
                                {match.opportunity.location ?? "Location unknown"}
                              </span>
                              <span className="inline-flex items-center gap-1">
                                <Calendar className="h-3.5 w-3.5" />
                                {match.opportunity.deadline
                                  ? `Deadline ${formatDate(match.opportunity.deadline)}`
                                  : "No deadline"}
                              </span>
                            </div>
                          </div>
                          <Badge variant="secondary" className="self-start sm:self-auto">
                            {match.status}
                          </Badge>
                        </Link>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {filteredMatches.length > 0 && (
                <>
                  <div ref={observerTarget} className="h-4" />
                  {isFetchingNextPage && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Sparkles className="h-4 w-4 animate-pulse" />
                      Loading more matches...
                    </div>
                  )}
                  {!hasNextPage && !isLoadingMatches && (
                    <div className="flex items-center justify-center py-6 border-t border-border/60">
                      <div className="text-sm text-muted-foreground">
                        You've reached the end.
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </DashboardLayout>
  );
}
