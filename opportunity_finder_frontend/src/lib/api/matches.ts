import apiClient from "@/lib/api-client";

export type MatchStatus = "ACTIVE" | "NOTIFIED" | "IGNORED" | "EXPIRED";

export type MatchOpportunity = {
    id: number;
    title: string;
    organization: string;
    source_url: string;
    deadline: string | null;
    op_type: string;
    domain: string;
    specialization: string;
    work_mode: string;
    employment_type: string;
    experience_level: string;
    location: string | null;
};

export type MatchListItem = {
    id: number;
    opportunity: MatchOpportunity;
    match_score: number;
    status: MatchStatus;
    created_at: string;
    updated_at: string;
};

export type MatchDetail = MatchListItem & {
    justification: string;
    stage1_passed: boolean;
    stage2_score: number | null;
    viewed_at: string | null;
    saved_at: string | null;
};

export type PaginatedResponse<T> = {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
};

export const matchesApi = {
    async list(status?: MatchStatus) {
        const response = await apiClient.get<PaginatedResponse<MatchListItem>>("/matches/", {
            params: status ? { status } : undefined,
        });
        return response.data.results ?? [];
    },

    async listPaginated(params?: { status?: MatchStatus; page?: number }) {
        const response = await apiClient.get<PaginatedResponse<MatchListItem>>("/matches/", {
            params,
        });
        return response.data;
    },
    async getById(id: number) {
        const response = await apiClient.get<MatchDetail>(`/matches/${id}/`);
        return response.data;
    },
};
