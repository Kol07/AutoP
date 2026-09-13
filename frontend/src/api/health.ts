import { apiRequest } from "./apiClient";

export interface HealthResponse {
    status: string;
}

export function fetchHealth(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health")
}