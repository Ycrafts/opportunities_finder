import apiClient from "@/lib/api-client";

export type NotificationMatchDetails = {
    id: number;
    score: number;
    justification: string;
    stage1_passed: boolean;
    stage2_score: number | null;
};

export type NotificationItem = {
    id: number;
    channel: string;
    status: string;
    subject: string;
    message: string;
    sent_at: string | null;
    delivered_at: string | null;
    viewed_at: string | null;
    saved_at: string | null;
    created_at: string;
    match_details: NotificationMatchDetails;
    opportunity_id: number;
    opportunity_title: string;
    organization: string;
};

export const notificationsApi = {
    async list() {
        const response = await apiClient.get<{ results: NotificationItem[] }>(
            "/notifications/"
        );
        return response.data.results ?? [];
    },
    async markViewed(id: number) {
        const response = await apiClient.post(`/notifications/${id}/mark_viewed/`);
        return response.data;
    },
    async markAllViewed() {
        const response = await apiClient.post("/notifications/mark_all_viewed/");
        return response.data;
    },
    async unreadCount() {
        const response = await apiClient.get<{ unread_count: number }>(
            "/notifications/unread_count/"
        );
        return response.data.unread_count ?? 0;
    },
};
