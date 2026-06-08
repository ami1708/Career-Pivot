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
import type { Artifact, ConnectorStatus, DashboardSummary, DiscoveryResponse, Job, JobStatus, PrepareApplicationResponse, Profile } from "./types/job";
import { ActionButton } from "./components/ActionButton";
import { JobBoard } from "./components/JobBoard";
import { JobDetail } from "./components/JobDetail";
import { ProfilePanel } from "./components/ProfilePanel";
import { SummaryBar } from "./components/SummaryBar";

const SOURCE_OPTIONS = [
  ["remotive", "Remotive"],
  ["remoteok", "RemoteOK"],
  ["greenhouse", "Greenhouse"],
  ["lever", "Lever"],
  ["linkedin", "LinkedIn"],
  ["instahyre", "Instahyre"],
  ["naukri", "Naukri"],
  ["indeed", "Indeed"],
  ["wellfound", "Wellfound"],
] as const;

const DEFAULT_SOURCES = SOURCE_OPTIONS.map(([value]) => value);

export default function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [connectors, setConnectors] = useState<ConnectorStatus | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [activeStatus, setActiveStatus] = useState<JobStatus>("new");
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>(DEFAULT_SOURCES);
  const [lastDiscovery, setLastDiscovery] = useState<DiscoveryResponse | null>(null);
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

  function toggleSource(source: string) {
    setSelectedSources((current) => (current.includes(source) ? current.filter((item) => item !== source) : [...current, source]));
  }

  function handleDiscovery() {
    runAction(
      () => discoverJobs(selectedSources.length ? selectedSources : undefined),
      (result) => {
        setLastDiscovery(result);
        return discoveryNotice(result);
      }
    );
  }

  async function handlePrepareApplication() {
    if (!selectedJob) {
      return;
    }
    const reviewWindow = window.open("about:blank", "_blank", "noopener,noreferrer");
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await prepareApplication(selectedJob.id);
      let copied = false;
      try {
        await navigator.clipboard.writeText(applicationPacket(selectedJob, result));
        copied = true;
      } catch {
        copied = false;
      }
      if (reviewWindow) {
        reviewWindow.location.href = result.job_url;
      }
      setNotice(
        `${result.message} ${reviewWindow ? "Opened the application page." : "Use the Open button to review the application page."} ${
          copied ? "Autofill answers were copied to clipboard." : "Autofill answers are available in the generated material."
        }`
      );
      await load();
      setArtifacts(await fetchArtifacts(selectedJob.id));
    } catch (err) {
      reviewWindow?.close();
      setError(err instanceof Error ? err.message : "Application preparation failed.");
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
                onClick={handleDiscovery}
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
          <div className="mt-4 border-t border-slate-100 pt-3">
            <p className="text-xs font-semibold uppercase text-slate-500">Discovery Sources</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {SOURCE_OPTIONS.map(([value, label]) => {
                const checked = selectedSources.includes(value);
                return (
                  <label
                    key={value}
                    className={`inline-flex min-h-9 cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm font-medium ${
                      checked
                        ? "border-emerald-600 bg-emerald-50 text-emerald-800"
                        : "border-slate-200 bg-slate-50 text-slate-600 hover:border-emerald-200"
                    }`}
                  >
                    <input className="size-4 accent-emerald-700" type="checkbox" checked={checked} onChange={() => toggleSource(value)} />
                    <span>{label}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </header>

        {(error || notice) && (
          <div className={error ? "flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700" : "flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"}>
            {error ? <AlertCircle className="mt-0.5 size-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 size-4 shrink-0" />}
            <span className="text-pretty">{error || notice}</span>
          </div>
        )}

        {lastDiscovery && (
          <section className="rounded-md border border-slate-200 bg-white p-4 text-sm shadow-sm">
            <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
              <h2 className="font-semibold text-slate-950">Last Discovery Run</h2>
              <p className="text-slate-600">
                {lastDiscovery.discovered} discovered · {lastDiscovery.accepted} matched · {lastDiscovery.skipped} skipped
              </p>
            </div>
            <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
              {Object.entries(lastDiscovery.sources).map(([source, stats]) => (
                <div key={source} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-800">{source}</span>
                    <span className="tabular-nums text-slate-600">{stats.discovered} found</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {stats.accepted} matched · {stats.skipped} skipped · {stats.attempts} attempts
                  </p>
                  {stats.errors.length > 0 && <p className="mt-1 line-clamp-2 text-xs text-red-600">{stats.errors[0]}</p>}
                </div>
              ))}
            </div>
            {lastDiscovery.errors.length > 0 && (
              <p className="mt-3 text-xs text-amber-700">
                Some sources were blocked or returned no readable results. Try fewer browser boards or log in with saved Playwright auth for those sites.
              </p>
            )}
          </section>
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
            onPrepare={handlePrepareApplication}
            onOutreach={() => selectedJob && runAction(() => sendOutreach(selectedJob.id), "Outreach processed.")}
            onStatus={(status) => selectedJob && runAction(() => updateJobStatus(selectedJob.id, status), "Status updated.")}
          />
        </div>
      </div>
    </main>
  );
}

function discoveryNotice(result: DiscoveryResponse) {
  const sourceCount = Object.keys(result.sources).length;
  const errorText = result.errors.length ? ` ${result.errors.length} source issue${result.errors.length === 1 ? "" : "s"} logged.` : "";
  return `Discovery completed across ${sourceCount} sources: ${result.discovered} jobs discovered, ${result.accepted} matched, ${result.skipped} skipped.${errorText}`;
}

function applicationPacket(job: Job, result: PrepareApplicationResponse) {
  const answers = Object.entries(result.answers)
    .map(([key, value]) => `${key}: ${formatAnswer(value)}`)
    .join("\n");
  return [
    "Career Pivot Application Packet",
    "",
    `Role: ${job.title}`,
    `Company: ${job.company}`,
    `Apply URL: ${result.job_url}`,
    result.resume_path ? `Resume: ${result.resume_path}` : "Resume: not loaded",
    "",
    "Autofill answers",
    answers || "No generated answers yet. Click Generate Material first for richer answers.",
  ].join("\n");
}

function formatAnswer(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "Not specified";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}
