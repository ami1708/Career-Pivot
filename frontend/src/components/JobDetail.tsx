import { ArrowUpRight, CircleDot, FileCheck2, Mail, Send, Sparkles, SquarePen, Trophy, XCircle } from "lucide-react";
import type { Artifact, Job } from "../types/job";
import { ActionButton } from "./ActionButton";
import { cn } from "../lib/utils";

type JobDetailProps = {
  job: Job | null;
  artifacts: Artifact[];
  busy: boolean;
  onGenerate: () => void;
  onPrepare: () => void;
  onOutreach: () => void;
  onStatus: (status: string) => void;
};

export function JobDetail({ job, artifacts, busy, onGenerate, onPrepare, onOutreach, onStatus }: JobDetailProps) {
  if (!job) {
    return (
      <aside className="w-full rounded-md border border-slate-200 bg-white p-5 shadow-sm lg:w-[28rem]">
        <p className="text-sm text-slate-600">Select a job to inspect score details and application material.</p>
      </aside>
    );
  }

  const breakdown = job.score_breakdown;
  const artifactPreview = artifacts[0];

  return (
    <aside className="flex w-full flex-col gap-5 rounded-md border border-slate-200 bg-white p-5 shadow-sm lg:sticky lg:top-4 lg:max-h-[calc(100dvh-2rem)] lg:w-[28rem] lg:overflow-auto">
      <div>
        <div className="flex items-center justify-between gap-3">
          <p className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold uppercase text-slate-600">{job.source}</p>
          <a
            className="inline-flex min-h-9 items-center gap-2 rounded-md border border-slate-200 px-2 py-1 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            href={job.url}
            target="_blank"
            rel="noreferrer"
          >
            Open
            <ArrowUpRight className="size-4" />
          </a>
        </div>
        <h2 className="mt-1 text-xl font-bold text-balance text-slate-950">{job.title}</h2>
        <p className="mt-1 text-sm text-slate-600">
          {job.company} · {job.remote ? "Remote" : job.location || "Location not listed"}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-700">Match Score</span>
          <span className="text-2xl font-bold tabular-nums text-slate-950">{job.score}</span>
        </div>
        <div className="mt-2 h-2 rounded-md bg-slate-100">
          <div
            className={cn("h-2 rounded-md", job.score >= 80 ? "bg-emerald-600" : job.score >= 60 ? "bg-amber-600" : "bg-slate-400")}
            style={{ width: `${Math.min(job.score, 100)}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-pretty text-slate-600">{job.rejection_reason || "Strong matches stay in the New Jobs lane for review."}</p>
      </div>

      <div className="space-y-2 text-sm">
        <Score label="Skills" value={breakdown.skill_overlap || 0} max={35} />
        <Score label="Experience" value={breakdown.experience_match || 0} max={20} />
        <Score label="Location" value={breakdown.location_match || 0} max={20} />
        <Score label="Seniority" value={breakdown.seniority_match || 0} max={15} />
        <Score label="Tech relevance" value={breakdown.tech_relevance || 0} max={10} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-900">Matched Skills</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {(breakdown.matched_skills || []).map((skill) => (
            <span key={skill} className="rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700">
              {skill}
            </span>
          ))}
        </div>
      </div>

      {(breakdown.notes || []).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Why It Scored This Way</h3>
          <div className="mt-2 space-y-2">
            {(breakdown.notes || []).map((note) => (
              <div key={note} className="flex gap-2 text-sm text-slate-600">
                <CircleDot className="mt-0.5 size-4 shrink-0 text-emerald-700" />
                <p className="text-pretty">{note}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-2">
        <ActionButton icon={<Sparkles className="size-4" />} onClick={onGenerate} disabled={busy} variant="primary">
          Generate Material
        </ActionButton>
        <ActionButton icon={<FileCheck2 className="size-4" />} onClick={onPrepare} disabled={busy}>
          Prepare + Open Apply
        </ActionButton>
        <ActionButton icon={<Send className="size-4" />} onClick={onOutreach} disabled={busy}>
          Draft or Send Outreach
        </ActionButton>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-900">Move Status</h3>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <ActionButton icon={<SquarePen className="size-4" />} onClick={() => onStatus("applied")} disabled={busy} variant="quiet">
            Applied
          </ActionButton>
          <ActionButton icon={<Mail className="size-4" />} onClick={() => onStatus("interviewing")} disabled={busy} variant="quiet">
            Interviewing
          </ActionButton>
          <ActionButton icon={<XCircle className="size-4" />} onClick={() => onStatus("rejected")} disabled={busy} variant="quiet">
            Rejected
          </ActionButton>
          <ActionButton icon={<Trophy className="size-4" />} onClick={() => onStatus("offers")} disabled={busy} variant="quiet">
            Offer
          </ActionButton>
        </div>
      </div>

      {artifactPreview && (
        <div>
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-slate-900">Latest Artifact</h3>
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{artifactPreview.kind.replace("_", " ")}</span>
          </div>
          <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">
            {artifactPreview.content.slice(0, 1800)}
          </pre>
        </div>
      )}
    </aside>
  );
}

function Score({ label, value, max }: { label: string; value: number; max: number }) {
  const percentage = Math.min(100, Math.round((value / max) * 100));
  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-slate-600">{label}</span>
        <span className="tabular-nums text-slate-950">
          {value}/{max}
        </span>
      </div>
      <div className="mt-1 h-1.5 rounded-md bg-slate-100">
        <div className="h-1.5 rounded-md bg-emerald-600" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}
