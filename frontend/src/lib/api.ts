import type { Artifact, AutoApplyResponse, ConnectorStatus, DashboardSummary, Job, Profile, ProfileUpdatePayload } from "../types/job";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchProfile() {
  return request<Profile>("/api/profile/current");
}

export function importLocalResume() {
  return request("/api/profile/resume/import-local", { method: "POST" });
}

export function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return uploadRequest<{ profile: Profile; extracted_keywords: string[] }>("/api/profile/resume", formData);
}

export function updateProfile(payload: ProfileUpdatePayload) {
  return request<Profile>("/api/profile/current", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchSummary() {
  return request<DashboardSummary>("/api/dashboard/summary");
}

export async function fetchJobs() {
  const payload = await request<{ jobs: Job[]; total: number }>("/api/jobs?limit=200");
  return payload.jobs;
}

export function discoverJobs() {
  return request("/api/jobs/discover", {
    method: "POST",
    body: JSON.stringify({ limit: 60 }),
  });
}

export function updateJobStatus(jobId: number, status: string) {
  return request<Job>(`/api/jobs/${jobId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function generateArtifacts(jobId: number) {
  return request<{ artifacts: Artifact[] }>(`/api/jobs/${jobId}/generate-artifacts`, { method: "POST" });
}

export function prepareApplication(jobId: number) {
  return request(`/api/jobs/${jobId}/apply/prepare`, { method: "POST" });
}

export function autoApplyJobs(limit = 10) {
  return request<AutoApplyResponse>("/api/applications/auto-apply", {
    method: "POST",
    body: JSON.stringify({ limit }),
  });
}

export function sendOutreach(jobId: number) {
  return request(`/api/jobs/${jobId}/outreach/send`, { method: "POST" });
}

export function fetchArtifacts(jobId: number) {
  return request<Artifact[]>(`/api/jobs/${jobId}/artifacts`);
}

export function fetchConnectors() {
  return request<ConnectorStatus>("/api/connectors");
}
