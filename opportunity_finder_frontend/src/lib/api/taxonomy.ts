import apiClient from "../api-client";
import type { Domain, Location, OpportunityType, Specialization } from "./match-config";

export const taxonomyApi = {
  getOpportunityTypes: async (): Promise<OpportunityType[]> => {
    const response = await apiClient.get<OpportunityType[]>("/opportunities/taxonomy/opportunity-types/");
    return response.data;
  },

  getDomains: async (): Promise<Domain[]> => {
    const response = await apiClient.get<Domain[]>("/opportunities/taxonomy/domains/");
    return response.data;
  },

  getSpecializations: async (): Promise<Specialization[]> => {
    const response = await apiClient.get<Specialization[]>("/opportunities/taxonomy/specializations/");
    return response.data;
  },

  getLocations: async (): Promise<Location[]> => {
    const response = await apiClient.get<Location[]>("/opportunities/taxonomy/locations/");
    return response.data;
  },
};

