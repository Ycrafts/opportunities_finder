import apiClient from "../api-client";

export interface OpportunityType {
  id: number;
  name: string;
}

export interface Domain {
  id: number;
  name: string;
  opportunity_type: OpportunityType;
}

export interface Specialization {
  id: number;
  name: string;
  domain: Domain;
}

export interface Location {
  id: number;
  name: string;
  parent: { id: number; name: string } | null;
}

export interface MatchConfig {
  threshold_score: number;
  notification_frequency: "INSTANT" | "DAILY" | "WEEKLY";
  notify_via_telegram: boolean;
  notify_via_email: boolean;
  notify_via_web_push: boolean;
  telegram_frequency: "INSTANT" | "DAILY" | "WEEKLY" | null;
  email_frequency: "INSTANT" | "DAILY" | "WEEKLY" | null;
  web_push_frequency: "INSTANT" | "DAILY" | "WEEKLY" | null;
  max_alerts_per_day: number | null;
  quiet_hours_start: string | null; // HH:MM format
  quiet_hours_end: string | null; // HH:MM format
  work_mode: "ANY" | "REMOTE" | "ONSITE" | "HYBRID";
  employment_type: "ANY" | "FULL_TIME" | "PART_TIME" | "CONTRACT" | "INTERNSHIP";
  experience_level: "ANY" | "STUDENT" | "GRADUATE" | "JUNIOR" | "MID" | "SENIOR";
  min_compensation: number | null;
  max_compensation: number | null;
  deadline_after: string | null; // ISO date
  deadline_before: string | null; // ISO date
  preferred_opportunity_types: OpportunityType[];
  muted_opportunity_types: OpportunityType[];
  preferred_domains: Domain[];
  preferred_specializations: Specialization[];
  preferred_locations: Location[];
  created_at: string;
  updated_at: string;
}

export interface UpdateMatchConfigRequest {
  threshold_score?: number;
  notification_frequency?: "INSTANT" | "DAILY" | "WEEKLY";
  notify_via_telegram?: boolean;
  notify_via_email?: boolean;
  notify_via_web_push?: boolean;
  telegram_frequency?: "INSTANT" | "DAILY" | "WEEKLY" | null;
  email_frequency?: "INSTANT" | "DAILY" | "WEEKLY" | null;
  web_push_frequency?: "INSTANT" | "DAILY" | "WEEKLY" | null;
  max_alerts_per_day?: number | null;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  work_mode?: "ANY" | "REMOTE" | "ONSITE" | "HYBRID";
  employment_type?: "ANY" | "FULL_TIME" | "PART_TIME" | "CONTRACT" | "INTERNSHIP";
  experience_level?: "ANY" | "STUDENT" | "GRADUATE" | "JUNIOR" | "MID" | "SENIOR";
  min_compensation?: number | null;
  max_compensation?: number | null;
  deadline_after?: string | null;
  deadline_before?: string | null;
  preferred_opportunity_types?: number[]; // IDs
  muted_opportunity_types?: number[]; // IDs
  preferred_domains?: number[]; // IDs
  preferred_specializations?: number[]; // IDs
  preferred_locations?: number[]; // IDs
}

export const matchConfigApi = {
  getConfig: async (): Promise<MatchConfig> => {
    const response = await apiClient.get<MatchConfig>("/config/me/");
    return response.data;
  },

  updateConfig: async (data: UpdateMatchConfigRequest): Promise<MatchConfig> => {
    const response = await apiClient.patch<MatchConfig>("/config/me/", data);
    return response.data;
  },
};

