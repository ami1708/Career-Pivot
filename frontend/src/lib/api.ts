import type {
  Artifact,
  AutoApplyResponse,
  ConnectorStatus,
  DashboardSummary,
  DiscoveryResponse,
  Job,
  PrepareApplicationResponse,
  Profile,
  ProfileUpdatePayload,
} from "../types/job";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? defaultApiBaseUrl();

function defaultApiBaseUrl() {
  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }
  const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
  return localHosts.has(window.location.hostname) ? "http://localhost:8000" : "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
    if (!response.ok) {
      throw new Error(await errorText(response));
    }
    return response.json() as Promise<T>;
  } catch (err) {
    throw normalizeFetchError(err);
  }
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await errorText(response));
    }
    return response.json() as Promise<T>;
  } catch (err) {
    throw normalizeFetchError(err);
  }
}

async function errorText(response: Response) {
  const text = await response.text();
  try {
    const payload = JSON.parse(text) as { detail?: unknown; message?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (typeof payload.message === "string") {
      return payload.message;
    }
  } catch {
    // Fall back to raw text below.
  }
  return text || `Request failed: ${response.status}`;
}

function normalizeFetchError(err: unknown) {
  if (err instanceof TypeError && err.message.toLowerCase().includes("failed to fetch")) {
    const target = API_BASE_URL || `${window.location.origin}/api`;
    const action = API_BASE_URL
      ? "Start the FastAPI server, then refresh Career Pivot."
      : "The hosted backend is not responding yet. Refresh in a moment, or check the Vercel backend deployment.";
    return new Error(`Backend is not reachable at ${target}. ${action}`);
  }
  return err instanceof Error ? err : new Error("Request failed.");
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

export function discoverJobs(sources?: string[]) {
  return request<DiscoveryResponse>("/api/jobs/discover", {
    method: "POST",
    body: JSON.stringify({ limit: 80, sources }),
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
  return request<PrepareApplicationResponse>(`/api/jobs/${jobId}/apply/prepare`, { method: "POST" });
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
