import { BriefcaseBusiness, Clock, FileCheck2, Gauge, MessageCircle, Target, Trophy, XCircle } from "lucide-react";
import type { DashboardSummary } from "../types/job";
import { cn } from "../lib/utils";

type SummaryBarProps = {
  summary: DashboardSummary | null;
};

const stats = [
  ["New", "new_jobs", BriefcaseBusiness, "Needs review", "sky"],
  ["Applied", "applied", FileCheck2, "Submitted", "emerald"],
  ["Interviews", "interviewing", MessageCircle, "Active loops", "amber"],
  ["Rejected", "rejected", XCircle, "Closed out", "rose"],
  ["Offers", "offers", Trophy, "Wins", "emerald"],
  ["Follow-ups", "follow_ups", Clock, "Needs nudge", "amber"],
] as const;

export function SummaryBar({ summary }: SummaryBarProps) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
      <div className="rounded-md border border-emerald-100 bg-white p-3 shadow-sm md:col-span-2">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-xs font-medium text-slate-500">Average Score</p>
            <p className="mt-1 text-3xl font-bold tabular-nums text-slate-950">{summary?.average_score ?? 0}</p>
          </div>
          <Gauge className="size-6 text-emerald-700" />
        </div>
        <div className="mt-3 h-2 rounded-md bg-slate-100">
          <div className="h-2 rounded-md bg-emerald-600" style={{ width: `${Math.min(summary?.average_score ?? 0, 100)}%` }} />
        </div>
      </div>

      <div className="rounded-md border border-emerald-100 bg-white p-3 shadow-sm md:col-span-2">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-xs font-medium text-slate-500">High-fit Jobs</p>
            <p className="mt-1 text-3xl font-bold tabular-nums text-slate-950">{summary?.high_score_jobs ?? 0}</p>
          </div>
          <Target className="size-6 text-emerald-700" />
        </div>
        <p className="mt-3 text-sm text-pretty text-slate-600">Matches at or above the configured 80% threshold.</p>
      </div>

      {stats.map(([label, key, Icon, helper, color]) => (
        <div key={key} className="rounded-md border border-slate-200 bg-white p-3 shadow-sm">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-xs font-medium text-slate-500">{label}</p>
            <Icon
              className={cn(
                "size-4",
                color === "sky" && "text-sky-700",
                color === "emerald" && "text-emerald-700",
                color === "amber" && "text-amber-700",
                color === "rose" && "text-rose-700"
              )}
            />
          </div>
          <p className="mt-2 text-2xl font-bold tabular-nums text-slate-950">{summary?.[key] ?? 0}</p>
          <p className="mt-1 truncate text-xs text-slate-500">{helper}</p>
        </div>
      ))}
    </div>
  );
}
