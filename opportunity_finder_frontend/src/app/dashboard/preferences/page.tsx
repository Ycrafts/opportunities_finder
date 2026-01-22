"use client";

import { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  Bell,
  Settings,
  Target,
  Sliders,
  Save,
  Loader2,
  X,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import {
  matchConfigApi,
  type MatchConfig,
  type UpdateMatchConfigRequest,
  type Domain,
  type Location,
  type OpportunityType,
  type Specialization,
} from "@/lib/api/match-config";
import { taxonomyApi } from "@/lib/api/taxonomy";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FadeIn } from "@/components/animations/fade-in";

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

export default function PreferencesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch match config
  const {
    data: config,
    isLoading: configLoading,
    error: configError,
  } = useQuery({
    queryKey: ["match-config"],
    queryFn: () => matchConfigApi.getConfig(),
    enabled: isAuthenticated,
  });

  // Fetch taxonomy data
  const { data: opportunityTypes = [] } = useQuery({
    queryKey: ["taxonomy", "opportunity-types"],
    queryFn: () => taxonomyApi.getOpportunityTypes(),
    enabled: isAuthenticated,
  });

  const { data: domains = [] } = useQuery({
    queryKey: ["taxonomy", "domains"],
    queryFn: () => taxonomyApi.getDomains(),
    enabled: isAuthenticated,
  });

  const { data: specializations = [] } = useQuery({
    queryKey: ["taxonomy", "specializations"],
    queryFn: () => taxonomyApi.getSpecializations(),
    enabled: isAuthenticated,
  });

  const { data: locations = [] } = useQuery({
    queryKey: ["taxonomy", "locations"],
    queryFn: () => taxonomyApi.getLocations(),
    enabled: isAuthenticated,
  });

  // Local state for form
  const [formData, setFormData] = useState<UpdateMatchConfigRequest>({});
  const [typeSearch, setTypeSearch] = useState("");
  const [domainSearchByType, setDomainSearchByType] = useState<Record<number, string>>({});
  const [specSearchByDomain, setSpecSearchByDomain] = useState<Record<number, string>>({});
  const [expandedTypes, setExpandedTypes] = useState<Record<number, boolean>>({});
  const [expandedDomains, setExpandedDomains] = useState<Record<number, boolean>>({});
  const [expandedLocations, setExpandedLocations] = useState<Record<number, boolean>>({});
  const [thresholdDraft, setThresholdDraft] = useState<number>(7.0);

  const locationById = useMemo(() => {
    return new Map(locations.map((loc) => [loc.id, loc]));
  }, [locations]);

  const ethiopiaRoot = useMemo(() => {
    return locations.find((loc) => loc.name === "Ethiopia" && !loc.parent);
  }, [locations]);

  const isEthiopiaLocation = (location: Location): boolean => {
    let current: Location | undefined = location;
    while (current) {
      if (current.name === "Ethiopia" && !current.parent) {
        return true;
      }
      current = current.parent ? locationById.get(current.parent.id) : undefined;
    }
    return false;
  };

  const remoteLocation = useMemo(() => {
    return locations.find((loc) => loc.name === "Remote" && !loc.parent);
  }, [locations]);

  // Initialize form data when config loads
  useEffect(() => {
    if (config) {
      setFormData({
        threshold_score: config.threshold_score,
        notification_frequency: config.notification_frequency,
        notify_via_telegram: config.notify_via_telegram,
        notify_via_email: config.notify_via_email,
        notify_via_web_push: config.notify_via_web_push,
        telegram_frequency: config.telegram_frequency,
        email_frequency: config.email_frequency,
        web_push_frequency: config.web_push_frequency,
        max_alerts_per_day: config.max_alerts_per_day,
        quiet_hours_start: config.quiet_hours_start,
        quiet_hours_end: config.quiet_hours_end,
        work_mode: config.work_mode,
        employment_type: config.employment_type,
        experience_level: config.experience_level,
        min_compensation: config.min_compensation,
        max_compensation: config.max_compensation,
        deadline_after: config.deadline_after,
        deadline_before: config.deadline_before,
        preferred_opportunity_types: config.preferred_opportunity_types.map(
          (t) => t.id
        ),
        muted_opportunity_types: config.muted_opportunity_types.map(
          (t) => t.id
        ),
        preferred_domains: config.preferred_domains.map((d) => d.id),
        preferred_specializations: config.preferred_specializations.map(
          (s) => s.id
        ),
        preferred_locations: config.preferred_locations.map((l) => l.id),
      });
      setThresholdDraft(config.threshold_score ?? 7.0);
    }
  }, [config]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateMatchConfigRequest) =>
      matchConfigApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["match-config"] });
      toast.success("Preferences updated successfully");
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail ||
        error?.message ||
        "Failed to update preferences";
      toast.error(message);
    },
  });

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  // Helper functions for multi-select
  const toggleSelection = (
    id: number,
    field:
      | "preferred_opportunity_types"
      | "muted_opportunity_types"
      | "preferred_domains"
      | "preferred_specializations"
      | "preferred_locations"
  ) => {
    setFormData((prev) => {
      const current = prev[field] || [];
      const newValue = current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id];
      return { ...prev, [field]: newValue };
    });
  };

  const updateDomainSearch = (typeId: number, value: string) => {
    setDomainSearchByType((prev) => ({ ...prev, [typeId]: value }));
  };

  const updateSpecSearch = (domainId: number, value: string) => {
    setSpecSearchByDomain((prev) => ({ ...prev, [domainId]: value }));
  };

  const domainsByType = useMemo(() => {
    const map = new Map<number, Domain[]>();
    opportunityTypes.forEach((type) => {
      map.set(
        type.id,
        domains.filter((domain) => domain.opportunity_type.id === type.id)
      );
    });
    return map;
  }, [opportunityTypes, domains]);

  const specsByDomain = useMemo(() => {
    const map = new Map<number, Specialization[]>();
    domains.forEach((domain) => {
      map.set(
        domain.id,
        specializations.filter((spec) => spec.domain.id === domain.id)
      );
    });
    return map;
  }, [domains, specializations]);

  const toggleExpanded = (
    updater: React.Dispatch<React.SetStateAction<Record<number, boolean>>>,
    id: number
  ) => {
    updater((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleOpportunityTypeSelection = (typeId: number) => {
    setFormData((prev) => {
      const types = new Set(prev.preferred_opportunity_types || []);
      const domainsSet = new Set(prev.preferred_domains || []);
      const specsSet = new Set(prev.preferred_specializations || []);
      const typeDomains = domainsByType.get(typeId) || [];
      const typeDomainIds = typeDomains.map((domain) => domain.id);
      const typeSpecIds = typeDomains.flatMap((domain) =>
        (specsByDomain.get(domain.id) || []).map((spec) => spec.id)
      );

      if (types.has(typeId)) {
        types.delete(typeId);
        typeDomainIds.forEach((id) => domainsSet.delete(id));
        typeSpecIds.forEach((id) => specsSet.delete(id));
      } else {
        types.add(typeId);
        typeDomainIds.forEach((id) => domainsSet.add(id));
        typeSpecIds.forEach((id) => specsSet.add(id));
      }

      return {
        ...prev,
        preferred_opportunity_types: Array.from(types),
        preferred_domains: Array.from(domainsSet),
        preferred_specializations: Array.from(specsSet),
      };
    });
  };

  const toggleDomainSelection = (domainId: number, typeId: number) => {
    setFormData((prev) => {
      const domainsSet = new Set(prev.preferred_domains || []);
      const specsSet = new Set(prev.preferred_specializations || []);
      const typesSet = new Set(prev.preferred_opportunity_types || []);
      const domainSpecs = specsByDomain.get(domainId) || [];
      const domainSpecIds = domainSpecs.map((spec) => spec.id);

      if (domainsSet.has(domainId)) {
        domainsSet.delete(domainId);
        domainSpecIds.forEach((id) => specsSet.delete(id));
      } else {
        domainsSet.add(domainId);
        typesSet.add(typeId);
        domainSpecIds.forEach((id) => specsSet.add(id));
      }

      return {
        ...prev,
        preferred_opportunity_types: Array.from(typesSet),
        preferred_domains: Array.from(domainsSet),
        preferred_specializations: Array.from(specsSet),
      };
    });
  };

  const toggleSpecializationSelection = (
    specId: number,
    domainId: number,
    typeId: number
  ) => {
    setFormData((prev) => {
      const specsSet = new Set(prev.preferred_specializations || []);
      const domainsSet = new Set(prev.preferred_domains || []);
      const typesSet = new Set(prev.preferred_opportunity_types || []);

      if (specsSet.has(specId)) {
        specsSet.delete(specId);
      } else {
        specsSet.add(specId);
        domainsSet.add(domainId);
        typesSet.add(typeId);
      }

      return {
        ...prev,
        preferred_opportunity_types: Array.from(typesSet),
        preferred_domains: Array.from(domainsSet),
        preferred_specializations: Array.from(specsSet),
      };
    });
  };


  const getChildLocations = (parentId: number): Location[] => {
    return locations.filter(
      (loc) => loc.parent?.id === parentId && isEthiopiaLocation(loc)
    );
  };

  const getLocationDescendantIds = (parentId: number): number[] => {
    const descendants: number[] = [];
    const stack = getChildLocations(parentId).map((loc) => loc.id);
    while (stack.length > 0) {
      const currentId = stack.pop()!;
      descendants.push(currentId);
      getChildLocations(currentId).forEach((child) => stack.push(child.id));
    }
    return descendants;
  };

  const getLocationAncestorIds = (locationId: number): number[] => {
    const ancestors: number[] = [];
    let current = locations.find((loc) => loc.id === locationId);
    while (current?.parent) {
      ancestors.push(current.parent.id);
      current = locations.find((loc) => loc.id === current?.parent?.id);
    }
    return ancestors;
  };

  const toggleLocationSelection = (locationId: number) => {
    setFormData((prev) => {
      const selected = new Set(prev.preferred_locations || []);
      const descendants = getLocationDescendantIds(locationId);
      const ancestors = getLocationAncestorIds(locationId);

      if (selected.has(locationId)) {
        selected.delete(locationId);
        descendants.forEach((id) => selected.delete(id));
      } else {
        selected.add(locationId);
        descendants.forEach((id) => selected.add(id));
        ancestors.forEach((id) => selected.add(id));
      }

      return { ...prev, preferred_locations: Array.from(selected) };
    });
  };

  const topLevelLocations = useMemo(() => {
    const ethiopiaChildren = ethiopiaRoot
      ? getChildLocations(ethiopiaRoot.id)
      : [];
    return remoteLocation ? [...ethiopiaChildren, remoteLocation] : ethiopiaChildren;
  }, [ethiopiaRoot, remoteLocation, locations]);

  // Get full path string for a location
  const getLocationPath = (location: Location): string => {
    const path = [location.name];
    let current = location;
    while (current.parent) {
      path.unshift(current.parent.name);
      // Find parent in locations array
      const parentLoc = locations.find((l) => l.id === current.parent!.id);
      if (parentLoc) {
        current = parentLoc;
      } else {
        break;
      }
    }
    return path.join(" / ");
  };

  if (isLoading || configLoading) {
    return (
      <DashboardLayout navItems={navItems} title="Match Preferences">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </DashboardLayout>
    );
  }

  if (!isAuthenticated) {
    router.push("/");
    return null;
  }

  if (configError) {
    return (
      <DashboardLayout navItems={navItems} title="Match Preferences">
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load preferences. Please try again.
            </p>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout navItems={navItems} title="Match Preferences">
      <div className="space-y-6 max-w-5xl">
        <FadeIn>
          <Card>
            <CardHeader>
              <CardTitle>Matching Threshold</CardTitle>
              <CardDescription>
                Set the minimum match score (3-9) for opportunities to be shown
                to you
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="threshold">Minimum Match Score</Label>
                  <span className="text-sm font-medium">
                    {thresholdDraft.toFixed(1)}/10
                  </span>
                </div>
                <input
                  id="threshold"
                  type="range"
                  min="3"
                  max="9"
                  step="0.1"
                  value={thresholdDraft}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value) || 3;
                    setThresholdDraft(value);
                    setFormData((prev) => ({
                      ...prev,
                      threshold_score: value,
                    }));
                  }}
                  className="w-full accent-black dark:accent-white"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>3</span>
                  <span>9</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn>
          <Card>
            <CardHeader>
              <CardTitle>Work Preferences</CardTitle>
              <CardDescription>
                Specify your preferred work arrangements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="work_mode">Work Mode</Label>
                  <Select
                    value={formData.work_mode || "ANY"}
                    onValueChange={(value) =>
                      setFormData((prev) => ({
                        ...prev,
                        work_mode: value as any,
                      }))
                    }
                  >
                    <SelectTrigger id="work_mode">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ANY">Any</SelectItem>
                      <SelectItem value="REMOTE">Remote</SelectItem>
                      <SelectItem value="ONSITE">Onsite</SelectItem>
                      <SelectItem value="HYBRID">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="employment_type">Employment Type</Label>
                  <Select
                    value={formData.employment_type || "ANY"}
                    onValueChange={(value) =>
                      setFormData((prev) => ({
                        ...prev,
                        employment_type: value as any,
                      }))
                    }
                  >
                    <SelectTrigger id="employment_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ANY">Any</SelectItem>
                      <SelectItem value="FULL_TIME">Full-time</SelectItem>
                      <SelectItem value="PART_TIME">Part-time</SelectItem>
                      <SelectItem value="CONTRACT">Contract</SelectItem>
                      <SelectItem value="INTERNSHIP">Internship</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="experience_level">Experience Level</Label>
                  <Select
                    value={formData.experience_level || "ANY"}
                    onValueChange={(value) =>
                      setFormData((prev) => ({
                        ...prev,
                        experience_level: value as any,
                      }))
                    }
                  >
                    <SelectTrigger id="experience_level">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ANY">Any</SelectItem>
                      <SelectItem value="STUDENT">Student</SelectItem>
                      <SelectItem value="GRADUATE">Graduate</SelectItem>
                      <SelectItem value="JUNIOR">Junior</SelectItem>
                      <SelectItem value="MID">Mid</SelectItem>
                      <SelectItem value="SENIOR">Senior</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn>
          <Card>
            <CardHeader>
              <CardTitle>Opportunity Preferences</CardTitle>
              <CardDescription>
                Select the types of opportunities you're interested in
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <Input
                    value={typeSearch}
                    onChange={(e) => setTypeSearch(e.target.value)}
                    placeholder="Search opportunity types"
                    className="h-9 sm:max-w-xs"
                  />
                </div>
                <div className="space-y-4">
                  {opportunityTypes
                    .filter((type) =>
                      type.name.toLowerCase().includes(typeSearch.toLowerCase())
                    )
                    .map((type) => {
                    const isTypeSelected =
                      !!formData.preferred_opportunity_types?.includes(type.id);
                    const domainSearch = domainSearchByType[type.id] || "";
                    const typeDomains = domains.filter(
                      (domain) =>
                        domain.opportunity_type.id === type.id &&
                        domain.name.toLowerCase().includes(domainSearch.toLowerCase())
                    );

                    return (
                      <div key={type.id} className="space-y-2">
                        <div className="flex items-center gap-2">
                          {typeDomains.length > 0 ? (
                            <button
                              type="button"
                              onClick={() => toggleExpanded(setExpandedTypes, type.id)}
                              className="h-5 w-5 text-muted-foreground hover:text-foreground"
                              aria-label={expandedTypes[type.id] ? "Collapse" : "Expand"}
                            >
                              {expandedTypes[type.id] ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </button>
                          ) : (
                            <span className="h-5 w-5" aria-hidden="true" />
                          )}
                          <label className="flex items-center gap-2 text-sm font-medium">
                            <input
                              type="checkbox"
                              className="h-4 w-4 rounded border-black text-black accent-black"
                              checked={isTypeSelected}
                              onChange={() => toggleOpportunityTypeSelection(type.id)}
                            />
                            {type.name}
                          </label>
                        </div>

                        {expandedTypes[type.id] && (
                          <div className="ml-6 space-y-3 border-l pl-4">
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                              <Input
                                value={domainSearch}
                                onChange={(e) => updateDomainSearch(type.id, e.target.value)}
                                placeholder={`Search ${type.name} domains`}
                                className="h-9 sm:max-w-xs"
                              />
                            </div>
                            {typeDomains.length === 0 ? (
                              <p className="text-sm text-muted-foreground">
                                No domains available for this type.
                              </p>
                            ) : (
                              typeDomains.map((domain) => {
                                const isDomainSelected =
                                  !!formData.preferred_domains?.includes(domain.id);
                                const domainSpecs = specializations.filter(
                                  (spec) => spec.domain.id === domain.id
                                );

                                return (
                                  <div key={domain.id} className="space-y-2">
                                    <div className="flex items-center gap-2">
                                      {domainSpecs.length > 0 ? (
                                        <button
                                          type="button"
                                          onClick={() => toggleExpanded(setExpandedDomains, domain.id)}
                                          className="h-5 w-5 text-muted-foreground hover:text-foreground"
                                          aria-label={expandedDomains[domain.id] ? "Collapse" : "Expand"}
                                        >
                                          {expandedDomains[domain.id] ? (
                                            <ChevronDown className="h-4 w-4" />
                                          ) : (
                                            <ChevronRight className="h-4 w-4" />
                                          )}
                                        </button>
                                      ) : (
                                        <span className="h-5 w-5" aria-hidden="true" />
                                      )}
                                      <label className="flex items-center gap-2 text-sm">
                                        <input
                                          type="checkbox"
                                          className="h-4 w-4 rounded border-black text-black accent-black"
                                          checked={isDomainSelected}
                                          onChange={() =>
                                            toggleDomainSelection(domain.id, type.id)
                                          }
                                        />
                                        {domain.name}
                                      </label>
                                    </div>

                                    {expandedDomains[domain.id] && (
                                      <div className="ml-6 space-y-2">
                                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                          <Input
                                            value={specSearchByDomain[domain.id] || ""}
                                            onChange={(e) =>
                                              updateSpecSearch(domain.id, e.target.value)
                                            }
                                            placeholder={`Search ${domain.name} specializations`}
                                            className="h-9 sm:max-w-xs"
                                          />
                                        </div>
                                        {domainSpecs.length === 0 ? (
                                          <p className="text-sm text-muted-foreground">
                                            No specializations for this domain.
                                          </p>
                                        ) : (
                                          domainSpecs.map((spec) => {
                                            const isSpecSelected =
                                              !!formData.preferred_specializations?.includes(
                                                spec.id
                                              );
                                            return (
                                              <label
                                                key={spec.id}
                                                className="flex items-center gap-2 text-sm"
                                              >
                                                <input
                                                  type="checkbox"
                                                  className="h-4 w-4 rounded border-black text-black accent-black"
                                                  checked={isSpecSelected}
                                                  onChange={() =>
                                                    toggleSpecializationSelection(
                                                      spec.id,
                                                      domain.id,
                                                      type.id
                                                    )
                                                  }
                                                />
                                                {spec.name}
                                              </label>
                                            );
                                          })
                                        )}
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                {formData.preferred_opportunity_types?.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No types selected. All types will be shown.
                  </p>
                )}
              </div>

              <div className="space-y-3">
                <Label>Muted Opportunity Types</Label>
                <div className="flex flex-wrap gap-2">
                  {opportunityTypes.map((type) => {
                    const isSelected =
                      formData.muted_opportunity_types?.includes(type.id);
                    return (
                      <Badge
                        key={type.id}
                        variant={isSelected ? "destructive" : "outline"}
                        className="cursor-pointer hover:bg-muted px-3 py-1"
                        onClick={() =>
                          toggleSelection(type.id, "muted_opportunity_types")
                        }
                      >
                        {type.name}
                      </Badge>
                    );
                  })}
                </div>
                <p className="text-sm text-muted-foreground">
                  Muted types will be excluded from your matches
                </p>
              </div>


              <div className="space-y-3">
                <Label>Preferred Locations</Label>
                
                {/* Nested locations list */}
                <div className="space-y-2">
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {topLevelLocations.length === 0 ? (
                      <p className="text-sm text-muted-foreground py-2">
                        No locations available.
                      </p>
                    ) : (
                      topLevelLocations.map((location) => {
                        const isSelected = formData.preferred_locations?.includes(
                          location.id
                        );
                        const children = getChildLocations(location.id);
                        return (
                          <div key={location.id} className="space-y-2">
                            <div className="flex items-center gap-2">
                              {children.length > 0 ? (
                                <button
                                  type="button"
                                  onClick={() => toggleExpanded(setExpandedLocations, location.id)}
                                  className="h-5 w-5 text-muted-foreground hover:text-foreground"
                                  aria-label={expandedLocations[location.id] ? "Collapse" : "Expand"}
                                >
                                  {expandedLocations[location.id] ? (
                                    <ChevronDown className="h-4 w-4" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4" />
                                  )}
                                </button>
                              ) : (
                                <span className="h-5 w-5" aria-hidden="true" />
                              )}
                              <label className="flex items-center gap-2 text-sm">
                                <input
                                  type="checkbox"
                                  className="h-4 w-4 rounded border-black text-black accent-black"
                                  checked={!!isSelected}
                                  onChange={() => toggleLocationSelection(location.id)}
                                />
                                {location.name}
                              </label>
                            </div>
                            {expandedLocations[location.id] && children.length > 0 && (
                              <div className="ml-6 space-y-2 border-l pl-4">
                                {children.map((child) => {
                                  const childSelected =
                                    formData.preferred_locations?.includes(child.id);
                                  const grandchildren = getChildLocations(child.id);
                                  return (
                                    <div key={child.id} className="space-y-2">
                                      <div className="flex items-center gap-2">
                                        {grandchildren.length > 0 ? (
                                          <button
                                            type="button"
                                            onClick={() =>
                                              toggleExpanded(setExpandedLocations, child.id)
                                            }
                                            className="h-5 w-5 text-muted-foreground hover:text-foreground"
                                            aria-label={expandedLocations[child.id] ? "Collapse" : "Expand"}
                                          >
                                            {expandedLocations[child.id] ? (
                                              <ChevronDown className="h-4 w-4" />
                                            ) : (
                                              <ChevronRight className="h-4 w-4" />
                                            )}
                                          </button>
                                        ) : (
                                          <span className="h-5 w-5" aria-hidden="true" />
                                        )}
                                        <label className="flex items-center gap-2 text-sm">
                                          <input
                                            type="checkbox"
                                            className="h-4 w-4 rounded border-black text-black accent-black"
                                            checked={!!childSelected}
                                            onChange={() => toggleLocationSelection(child.id)}
                                          />
                                          {child.name}
                                        </label>
                                      </div>
                                      {expandedLocations[child.id] && grandchildren.length > 0 && (
                                        <div className="ml-6 space-y-2 border-l pl-4">
                                          {grandchildren.map((grandchild) => {
                                            const grandchildSelected =
                                              formData.preferred_locations?.includes(
                                                grandchild.id
                                              );
                                            return (
                                              <label
                                                key={grandchild.id}
                                                className="flex items-center gap-2 text-sm"
                                              >
                                                <input
                                                  type="checkbox"
                                                  className="h-4 w-4 rounded border-black text-black accent-black"
                                                  checked={!!grandchildSelected}
                                                  onChange={() => toggleLocationSelection(grandchild.id)}
                                                />
                                                {grandchild.name}
                                              </label>
                                            );
                                          })}
                                        </div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                  
                  {/* Show selected locations summary */}
                  {formData.preferred_locations && formData.preferred_locations.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-sm font-medium mb-2">
                        Selected Locations ({formData.preferred_locations.length}):
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {formData.preferred_locations.map((locId) => {
                          const loc = locations.find((l) => l.id === locId);
                          if (!loc) return null;
                          return (
                            <Badge
                              key={locId}
                              variant="default"
                              className="px-2 py-1"
                            >
                              {getLocationPath(loc)}
                              <button
                                type="button"
                                onClick={() => {
                                  setFormData((prev) => ({
                                    ...prev,
                                    preferred_locations: prev.preferred_locations?.filter(
                                      (id) => id !== locId
                                    ) || [],
                                  }));
                                }}
                                className="ml-2 hover:bg-primary/80 rounded-full w-4 h-4 flex items-center justify-center"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {(!formData.preferred_locations || formData.preferred_locations.length === 0) && (
                    <p className="text-sm text-muted-foreground">
                      No locations selected. All locations will be shown.
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn>
          <Card>
            <CardHeader>
              <CardTitle>Compensation & Deadlines</CardTitle>
              <CardDescription>
                Set your compensation and deadline preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="min_compensation">Minimum Compensation</Label>
                  <Input
                    id="min_compensation"
                    type="number"
                    placeholder="Leave empty for any"
                    value={formData.min_compensation ?? ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        min_compensation: e.target.value
                          ? parseInt(e.target.value)
                          : null,
                      }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max_compensation">Maximum Compensation</Label>
                  <Input
                    id="max_compensation"
                    type="number"
                    placeholder="Leave empty for any"
                    value={formData.max_compensation ?? ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        max_compensation: e.target.value
                          ? parseInt(e.target.value)
                          : null,
                      }))
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="deadline_after">Deadline After</Label>
                  <Input
                    id="deadline_after"
                    type="date"
                    value={
                      formData.deadline_after
                        ? formData.deadline_after.split("T")[0]
                        : ""
                    }
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        deadline_after: e.target.value
                          ? `${e.target.value}T00:00:00Z`
                          : null,
                      }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="deadline_before">Deadline Before</Label>
                  <Input
                    id="deadline_before"
                    type="date"
                    value={
                      formData.deadline_before
                        ? formData.deadline_before.split("T")[0]
                        : ""
                    }
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        deadline_before: e.target.value
                          ? `${e.target.value}T00:00:00Z`
                          : null,
                      }))
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn>
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
              <CardDescription>
                Configure how and when you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label>Notification Channels</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="notify_telegram"
                      checked={formData.notify_via_telegram ?? false}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          notify_via_telegram: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-black text-black accent-black"
                    />
                    <Label htmlFor="notify_telegram" className="cursor-pointer">
                      Telegram
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="notify_email"
                      checked={formData.notify_via_email ?? false}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          notify_via_email: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-black text-black accent-black"
                    />
                    <Label htmlFor="notify_email" className="cursor-pointer">
                      Email
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="notify_web_push"
                      checked={formData.notify_via_web_push ?? false}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          notify_via_web_push: e.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-black text-black accent-black"
                    />
                    <Label htmlFor="notify_web_push" className="cursor-pointer">
                      Web Push
                    </Label>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notification_frequency">
                  Default Notification Frequency
                </Label>
                <Select
                  value={formData.notification_frequency || "INSTANT"}
                  onValueChange={(value) =>
                    setFormData((prev) => ({
                      ...prev,
                      notification_frequency: value as any,
                    }))
                  }
                >
                  <SelectTrigger id="notification_frequency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="INSTANT">Instant</SelectItem>
                    <SelectItem value="DAILY">Daily</SelectItem>
                    <SelectItem value="WEEKLY">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_alerts_per_day">Max Alerts Per Day</Label>
                <Input
                  id="max_alerts_per_day"
                  type="number"
                  min="1"
                  placeholder="Leave empty for unlimited"
                  value={formData.max_alerts_per_day ?? ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      max_alerts_per_day: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    }))
                  }
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="quiet_hours_start">Quiet Hours Start</Label>
                  <Input
                    id="quiet_hours_start"
                    type="time"
                    value={formData.quiet_hours_start?.slice(0, 5) ?? ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        quiet_hours_start: e.target.value
                          ? `${e.target.value}:00`
                          : null,
                      }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="quiet_hours_end">Quiet Hours End</Label>
                  <Input
                    id="quiet_hours_end"
                    type="time"
                    value={formData.quiet_hours_end?.slice(0, 5) ?? ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        quiet_hours_end: e.target.value
                          ? `${e.target.value}:00`
                          : null,
                      }))
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn>
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => {
                if (config) {
                  setFormData({
                    threshold_score: config.threshold_score,
                    notification_frequency: config.notification_frequency,
                    notify_via_telegram: config.notify_via_telegram,
                    notify_via_email: config.notify_via_email,
                    notify_via_web_push: config.notify_via_web_push,
                    telegram_frequency: config.telegram_frequency,
                    email_frequency: config.email_frequency,
                    web_push_frequency: config.web_push_frequency,
                    max_alerts_per_day: config.max_alerts_per_day,
                    quiet_hours_start: config.quiet_hours_start,
                    quiet_hours_end: config.quiet_hours_end,
                    work_mode: config.work_mode,
                    employment_type: config.employment_type,
                    experience_level: config.experience_level,
                    min_compensation: config.min_compensation,
                    max_compensation: config.max_compensation,
                    deadline_after: config.deadline_after,
                    deadline_before: config.deadline_before,
                    preferred_opportunity_types:
                      config.preferred_opportunity_types.map((t) => t.id),
                    muted_opportunity_types: config.muted_opportunity_types.map(
                      (t) => t.id
                    ),
                    preferred_domains: config.preferred_domains.map(
                      (d) => d.id
                    ),
                    preferred_specializations:
                      config.preferred_specializations.map((s) => s.id),
                    preferred_locations: config.preferred_locations.map(
                      (l) => l.id
                    ),
                  });
                }
              }}
            >
              Reset
            </Button>
            <Button onClick={handleSave} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Preferences
                </>
              )}
            </Button>
          </div>
        </FadeIn>
      </div>
    </DashboardLayout>
  );
}
