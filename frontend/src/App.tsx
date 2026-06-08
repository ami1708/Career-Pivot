import { AlertCircle, Bot, CheckCircle2, RefreshCcw, Search } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  discoverJobs,
  autoApplyJobs,
  fetchArtifacts,
  fetchConnectors,
  fetchJobs,
  fetchProfile,
  fetchSummary,
  generateArtifacts,
  prepareApplication,
  sendOutreach,
  updateJobStatus,
} from "./lib/api";
import type { Artifact, ConnectorStatus, DashboardSummary, Job, JobStatus, Profile } from "./types/job";
import { ActionButton } from "./components/ActionButton";
import { JobBoard } from "./components/JobBoard";
import { JobDetail } from "./components/JobDetail";
import { ProfilePanel } from "./components/ProfilePanel";
import { SummaryBar } from "./components/SummaryBar";

export default function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [connectors, setConnectors] = useState<ConnectorStatus | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [activeStatus, setActiveStatus] = useState<JobStatus>("new");
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const selectedJob = useMemo(() => jobs.find((job) => job.id === selectedJobId) || null, [jobs, selectedJobId]);
  const activeJobs = useMemo(() => jobs.filter((job) => job.status === activeStatus), [jobs, activeStatus]);

  const load = useCallback(async () => {
    setError(null);
    const [profileData, summaryData, jobsData, connectorData] = await Promise.all([
      fetchProfile(),
      fetchSummary(),
      fetchJobs(),
      fetchConnectors(),
    ]);
    setProfile(profileData);
    setSummary(summaryData);
    setJobs(jobsData);
    setConnectors(connectorData);
    if (!selectedJobId && jobsData.length > 0) {
      setSelectedJobId(jobsData.find((job) => job.status === activeStatus)?.id || jobsData[0].id);
    }
  }, [activeStatus, selectedJobId]);

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [load]);

  useEffect(() => {
    if (!selectedJobId) {
      setArtifacts([]);
      return;
    }
    fetchArtifacts(selectedJobId)
      .then(setArtifacts)
      .catch(() => setArtifacts([]));
  }, [selectedJobId]);

  useEffect(() => {
    if (selectedJob && selectedJob.status === activeStatus) {
      return;
    }
    setSelectedJobId(activeJobs[0]?.id || null);
  }, [activeJobs, activeStatus, selectedJob]);

  async function runAction<T>(action: () => Promise<T>, success: string | ((result: T) => string)) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await action();
      setNotice(typeof success === "function" ? success(result) : success);
      await load();
      if (selectedJobId) {
        setArtifacts(await fetchArtifacts(selectedJobId));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-dvh flex-col bg-[#f3f7f6] lg:flex-row">
      <ProfilePanel profile={profile} connectors={connectors} onProfileChanged={load} />
      <div className="flex min-w-0 flex-1 flex-col gap-5 p-4 lg:p-5">
        <header className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold uppercase text-emerald-700">
                <span className="size-2 rounded-full bg-emerald-500" />
                Job match workspace
              </div>
              <h1 className="mt-2 text-2xl font-bold text-balance text-slate-950">Career Pivot</h1>
              <p className="mt-1 text-sm text-pretty text-slate-600">Application pipeline for curated software roles, tailored material, and tracking.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <ActionButton
                icon={<Search className="size-4" />}
                onClick={() => runAction(discoverJobs, "Discovery completed.")}
                disabled={busy}
                variant="primary"
              >
                Run Discovery
              </ActionButton>
              <ActionButton
                icon={<Bot className="size-4" />}
                onClick={() => {
                  const confirmed = window.confirm(
                    "Auto Apply will process high-scoring new jobs. In live mode it may submit supported application forms."
                  );
                  if (!confirmed) {
                    return;
                  }
                  runAction(() => autoApplyJobs(10), (result) => {
                    const mode = result.dry_run ? "safe mode" : "live mode";
                    return `Auto apply processed ${result.processed} jobs in ${mode}: ${result.submitted} submitted, ${result.prepared} prepared, ${result.failed} failed.`;
                  });
                }}
                disabled={busy}
                title="Process high-scoring new jobs"
              >
                Auto Apply
              </ActionButton>
              <ActionButton icon={<RefreshCcw className="size-4" />} onClick={() => runAction(load, "Dashboard refreshed.")} disabled={busy}>
                Refresh
              </ActionButton>
            </div>
          </div>
        </header>

        {(error || notice) && (
          <div className={error ? "flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700" : "flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"}>
            {error ? <AlertCircle className="mt-0.5 size-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 size-4 shrink-0" />}
            <span className="text-pretty">{error || notice}</span>
          </div>
        )}

        <SummaryBar summary={summary} />

        <div className="flex min-w-0 flex-1 flex-col gap-4 lg:flex-row">
          <JobBoard
            jobs={jobs}
            selectedJob={selectedJob}
            activeStatus={activeStatus}
            onStatusChange={setActiveStatus}
            onSelectJob={(job) => setSelectedJobId(job.id)}
          />
          <JobDetail
            job={selectedJob}
            artifacts={artifacts}
            busy={busy}
            onGenerate={() => selectedJob && runAction(() => generateArtifacts(selectedJob.id), "Application material generated.")}
            onPrepare={() => selectedJob && runAction(() => prepareApplication(selectedJob.id), "Application package prepared.")}
            onOutreach={() => selectedJob && runAction(() => sendOutreach(selectedJob.id), "Outreach processed.")}
            onStatus={(status) => selectedJob && runAction(() => updateJobStatus(selectedJob.id, status), "Status updated.")}
          />
        </div>
      </div>
    </main>
  );
}
