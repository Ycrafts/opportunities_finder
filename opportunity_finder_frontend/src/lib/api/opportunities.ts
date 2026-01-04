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

export interface Opportunity {
  id: number;
  title: string;
  organization: string;
  description_en: string;
  op_type: OpportunityType;
  domain: Domain;
  specialization: Specialization;
  location: Location | null;
  work_mode: string;
  is_remote: boolean;
  employment_type: string;
  experience_level: string;
  min_compensation: number | null;
  max_compensation: number | null;
  deadline: string | null;
  status: string;
  source_url: string;
  metadata: Record<string, any>;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OpportunityListParams {
  q?: string;
  op_type?: number;
  domain?: number;
  specialization?: number;
  location?: number;
  is_remote?: boolean;
  status?: string;
  page?: number;
  experience_level?: string;
  work_mode?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const opportunitiesApi = {
  async list(
    params?: OpportunityListParams
  ): Promise<PaginatedResponse<Opportunity>> {
    const response = await apiClient.get<PaginatedResponse<Opportunity>>(
      "/opportunities/",
      {
        params,
      }
    );
    return response.data;
  },

  async getById(id: number): Promise<Opportunity> {
    const response = await apiClient.get<Opportunity>(`/opportunities/${id}/`);
    return response.data;
  },
};

