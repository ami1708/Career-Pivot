import { Building2, ExternalLink, MapPin, Radar, SearchX } from "lucide-react";
import type { MouseEvent } from "react";
import type { Job, JobStatus } from "../types/job";
import { cn } from "../lib/utils";

type JobBoardProps = {
  jobs: Job[];
  selectedJob: Job | null;
  activeStatus: JobStatus;
  onStatusChange: (status: JobStatus) => void;
  onSelectJob: (job: Job) => void;
};

const statusLabels: Array<[JobStatus, string]> = [
  ["new", "New Jobs"],
  ["applied", "Applied"],
  ["interviewing", "Interviewing"],
  ["rejected", "Rejected"],
  ["offers", "Offers"],
  ["follow_up", "Follow-ups"],
  ["skipped", "Skipped"],
];

export function JobBoard({ jobs, selectedJob, activeStatus, onStatusChange, onSelectJob }: JobBoardProps) {
  const filteredJobs = jobs.filter((job) => job.status === activeStatus).sort((a, b) => b.score - a.score);
  const laneAverage =
    filteredJobs.length > 0 ? Math.round(filteredJobs.reduce((total, job) => total + job.score, 0) / filteredJobs.length) : 0;

  return (
    <section className="min-w-0 flex-1">
      <div className="flex flex-col gap-3 rounded-md border border-slate-200 bg-white p-3 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-950">Matched Jobs</h2>
            <p className="text-sm text-slate-500">
              {filteredJobs.length} jobs · lane average <span className="tabular-nums">{laneAverage}</span>
            </p>
          </div>
          <Radar className="size-5 text-emerald-700" />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
        {statusLabels.map(([status, label]) => {
          const count = jobs.filter((job) => job.status === status).length;
          return (
            <button
              key={status}
              className={cn(
                "inline-flex min-h-10 shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium",
                "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2",
                activeStatus === status
                  ? "border-emerald-600 bg-emerald-600 text-white"
                  : "border-slate-200 bg-slate-50 text-slate-700 hover:border-emerald-200 hover:bg-emerald-50"
              )}
              onClick={() => onStatusChange(status)}
              type="button"
            >
              <span>{label}</span>
              <span className="tabular-nums">{count}</span>
            </button>
          );
        })}
        </div>
      </div>

      <div className="mt-3 grid gap-3">
        {filteredJobs.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
            <SearchX className="mx-auto size-8 text-slate-400" />
            <h3 className="mt-3 text-sm font-bold text-slate-950">No jobs in this lane</h3>
            <p className="mt-1 text-sm text-pretty text-slate-600">Matching roles will appear here as the search progresses.</p>
          </div>
        ) : (
          filteredJobs.map((job) => {
            const matchedSkills = (job.score_breakdown.matched_skills || []).map((skill) => skill.toLowerCase());
            const secondarySkills = job.skills.filter((skill) => !matchedSkills.includes(skill.toLowerCase())).slice(0, 5);
            return (
            <button
              key={job.id}
              className={cn(
                "rounded-md border bg-white p-4 text-left shadow-sm transition-colors hover:border-emerald-200 hover:bg-emerald-50/40",
                "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2",
                selectedJob?.id === job.id ? "border-emerald-500 shadow-md" : "border-slate-200"
              )}
              onClick={() => onSelectJob(job)}
              type="button"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold uppercase text-slate-600">
                      {job.source}
                    </span>
                    {job.remote && <span className="rounded-md bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">Remote</span>}
                  </div>
                  <h3 className="line-clamp-2 text-base font-bold text-balance text-slate-950">{job.title}</h3>
                  <p className="mt-1 flex items-center gap-2 truncate text-sm text-slate-600">
                    <Building2 className="size-4 shrink-0" />
                    <span className="truncate">{job.company}</span>
                  </p>
                </div>
                <div
                  className={cn(
                    "rounded-md px-2 py-1 text-sm font-semibold tabular-nums",
                    job.score >= 80 ? "bg-emerald-100 text-emerald-800" : job.score >= 60 ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"
                  )}
                >
                  {job.score}
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2 text-sm text-slate-500">
                <MapPin className="size-4 shrink-0" />
                <span className="truncate">{job.remote ? "Remote" : job.location || "Location not listed"}</span>
              </div>
              <p className="mt-3 line-clamp-3 text-sm text-pretty text-slate-600">{job.description || "No description captured."}</p>
              <div className="mt-3 h-1.5 rounded-md bg-slate-100">
                <div
                  className={cn("h-1.5 rounded-md", job.score >= 80 ? "bg-emerald-600" : job.score >= 60 ? "bg-amber-600" : "bg-slate-400")}
                  style={{ width: `${Math.min(job.score, 100)}%` }}
                />
              </div>
              <div className="mt-3 flex items-center justify-between gap-3">
                <div className="flex min-w-0 flex-wrap gap-1">
                  {matchedSkills.slice(0, 5).map((skill) => (
                    <span key={skill} className="rounded-md bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">
                      {skill}
                    </span>
                  ))}
                  {secondarySkills.map((skill) => (
                    <span key={skill} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                      {skill}
                    </span>
                  ))}
                </div>
                <a
                  className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-slate-500 hover:bg-white hover:text-emerald-700"
                  href={job.url}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Open ${job.title}`}
                  onClick={(event: MouseEvent<HTMLAnchorElement>) => event.stopPropagation()}
                >
                  <ExternalLink className="size-4" />
                </a>
              </div>
            </button>
            );
          })
        )}
      </div>
    </section>
  );
}
