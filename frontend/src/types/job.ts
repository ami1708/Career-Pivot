export type JobStatus = "new" | "applied" | "interviewing" | "rejected" | "offers" | "follow_up" | "skipped";

export type Job = {
  id: number;
  source: string;
  external_id: string | null;
  url: string;
  title: string;
  company: string;
  location: string | null;
  remote: boolean;
  description: string | null;
  requirements: string[];
  skills: string[];
  seniority: string | null;
  employment_type: string | null;
  score: number;
  score_breakdown: {
    skill_overlap?: number;
    experience_match?: number;
    location_match?: number;
    seniority_match?: number;
    tech_relevance?: number;
    matched_skills?: string[];
    missing_core_skills?: string[];
    notes?: string[];
  };
  status: JobStatus;
  rejection_reason: string | null;
  recruiter_name: string | null;
  recruiter_email: string | null;
  discovered_at: string;
  applied_at: string | null;
  updated_at: string;
};

export type Profile = {
  id: number;
  name: string;
  current_role: string | null;
  experience_years: number;
  skills: string[];
  preferred_roles: string[];
  preferred_locations: string[];
  resume_text?: string | null;
  profile_json?: Record<string, unknown>;
  source_resume_path: string | null;
};

export type ProfileUpdatePayload = {
  name?: string;
  current_role?: string | null;
  experience_years?: number;
  skills?: string[];
  preferred_roles?: string[];
  preferred_locations?: string[];
};

export type DashboardSummary = {
  new_jobs: number;
  applied: number;
  interviewing: number;
  rejected: number;
  offers: number;
  follow_ups: number;
  skipped: number;
  average_score: number;
  high_score_jobs: number;
};

export type Artifact = {
  id: number;
  job_id: number;
  kind: string;
  content: string;
  file_path: string | null;
  created_at: string;
};

export type ConnectorStatus = Record<string, { available: boolean; mode: string }>;

export type AutoApplyJobResult = {
  job_id: number;
  title: string;
  company: string;
  source: string;
  score: number;
  application_id: number | null;
  status: string;
  submitted: boolean;
  dry_run: boolean;
  message: string;
};

export type AutoApplyResponse = {
  processed: number;
  submitted: number;
  prepared: number;
  skipped: number;
  failed: number;
  dry_run: boolean;
  run_id: number | null;
  results: AutoApplyJobResult[];
};
