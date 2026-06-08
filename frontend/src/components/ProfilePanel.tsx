import { BriefcaseBusiness, CheckCircle2, Database, FileUp, MapPin, Mail, Monitor, Save, Sheet, Target, Upload, UserRound } from "lucide-react";
import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import { importLocalResume, updateProfile, uploadResume } from "../lib/api";
import type { ConnectorStatus, Profile } from "../types/job";
import { cn } from "../lib/utils";

type ProfilePanelProps = {
  profile: Profile | null;
  connectors: ConnectorStatus | null;
  onProfileChanged: () => Promise<void>;
};

type ProfileForm = {
  name: string;
  currentRole: string;
  experienceYears: string;
  skills: string;
  preferredRoles: string;
  preferredLocations: string;
};

const connectorIcons = {
  gmail: Mail,
  google_sheets: Sheet,
  linkedin: UserRound,
  browser_automation: Monitor,
  calendar: CheckCircle2,
};

export function ProfilePanel({ profile, connectors, onProfileChanged }: ProfilePanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [form, setForm] = useState<ProfileForm>(() => toForm(profile));
  const [busyAction, setBusyAction] = useState<"upload" | "local" | "save" | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);

  useEffect(() => {
    setForm(toForm(profile));
  }, [profile]);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setPanelError(null);
    setPanelMessage(null);
    setBusyAction("upload");
    try {
      await uploadResume(file);
      await onProfileChanged();
      setPanelMessage(`Uploaded ${file.name}`);
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Resume upload failed.");
    } finally {
      setBusyAction(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handleLocalResume() {
    setPanelError(null);
    setPanelMessage(null);
    setBusyAction("local");
    try {
      await importLocalResume();
      await onProfileChanged();
      setPanelMessage("Saved resume imported.");
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Resume import failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPanelError(null);
    setPanelMessage(null);
    setBusyAction("save");
    try {
      await updateProfile({
        name: form.name.trim(),
        current_role: form.currentRole.trim(),
        experience_years: Number(form.experienceYears) || 0,
        skills: parseList(form.skills),
        preferred_roles: parseList(form.preferredRoles),
        preferred_locations: parseList(form.preferredLocations),
      });
      await onProfileChanged();
      setPanelMessage("Profile saved.");
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : "Profile update failed.");
    } finally {
      setBusyAction(null);
    }
  }

  const busy = busyAction !== null;

  return (
    <aside className="flex w-full flex-col gap-5 border-b border-slate-200 bg-white p-5 lg:w-[24rem] lg:border-b-0 lg:border-r">
      <section className="rounded-md border border-emerald-100 bg-emerald-50 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase text-slate-500">Candidate</p>
            <h1 className="mt-1 truncate text-2xl font-bold text-balance text-slate-950">{profile?.name || "Amisha Negi"}</h1>
            <p className="mt-1 text-sm text-pretty text-slate-600">
              {profile?.current_role || "SDE-2"} · {profile?.experience_years || 4}+ years
            </p>
          </div>
          <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-white text-emerald-700 shadow-sm">
            <UserRound className="size-5" />
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
          <div className="rounded-md border border-slate-200 bg-white p-3">
            <p className="text-xs text-slate-500">Threshold</p>
            <p className="mt-1 font-semibold tabular-nums text-slate-950">80%</p>
          </div>
          <div className="rounded-md border border-slate-200 bg-white p-3">
            <p className="text-xs text-slate-500">Apply Mode</p>
            <p className="mt-1 font-semibold text-slate-950">Guarded</p>
          </div>
        </div>
      </section>

      <section className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <FileUp className="size-4 text-emerald-700" />
          Resume
        </h2>
        <p className="mt-1 truncate text-xs text-slate-500">{profile?.source_resume_path || "No resume loaded"}</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <input ref={fileInputRef} className="sr-only" type="file" accept="application/pdf,.pdf" onChange={handleUpload} disabled={busy} />
          <button
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-emerald-600 bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            <Upload className="size-4" />
            {busyAction === "upload" ? "Uploading" : "Upload PDF"}
          </button>
          <button
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-900 shadow-sm hover:border-emerald-200 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            onClick={handleLocalResume}
            type="button"
          >
            <FileUp className="size-4" />
            {busyAction === "local" ? "Importing" : "Use Saved"}
          </button>
        </div>
        {(panelMessage || panelError) && (
          <div
            className={cn(
              "mt-3 rounded-md border p-2 text-sm",
              panelError ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"
            )}
          >
            {panelError || panelMessage}
          </div>
        )}
      </section>

      <form className="rounded-md border border-slate-200 bg-white p-4 shadow-sm" onSubmit={handleSave}>
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Target className="size-4 text-emerald-700" />
          Profile
        </h2>
        <div className="mt-3 grid gap-3">
          <Field label="Name">
            <input
              className={inputClass}
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              disabled={busy}
            />
          </Field>
          <div className="grid grid-cols-[1fr_6.5rem] gap-2">
            <Field label="Current Role">
              <input
                className={inputClass}
                value={form.currentRole}
                onChange={(event) => setForm((current) => ({ ...current, currentRole: event.target.value }))}
                disabled={busy}
              />
            </Field>
            <Field label="Years">
              <input
                className={inputClass}
                min="0"
                step="0.5"
                type="number"
                value={form.experienceYears}
                onChange={(event) => setForm((current) => ({ ...current, experienceYears: event.target.value }))}
                disabled={busy}
              />
            </Field>
          </div>
          <Field label="Skills">
            <textarea
              className={textareaClass}
              rows={3}
              value={form.skills}
              onChange={(event) => setForm((current) => ({ ...current, skills: event.target.value }))}
              disabled={busy}
            />
          </Field>
          <Field label="Target Roles">
            <textarea
              className={textareaClass}
              rows={3}
              value={form.preferredRoles}
              onChange={(event) => setForm((current) => ({ ...current, preferredRoles: event.target.value }))}
              disabled={busy}
            />
          </Field>
          <Field label="Target Locations">
            <textarea
              className={textareaClass}
              rows={2}
              value={form.preferredLocations}
              onChange={(event) => setForm((current) => ({ ...current, preferredLocations: event.target.value }))}
              disabled={busy}
            />
          </Field>
          <button
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-emerald-700 bg-emerald-700 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            type="submit"
          >
            <Save className="size-4" />
            {busyAction === "save" ? "Saving" : "Save Profile"}
          </button>
        </div>
      </form>

      <section>
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Database className="size-4 text-slate-700" />
          Integrations
        </h2>
        <div className="mt-2 space-y-2">
          {connectors &&
            Object.entries(connectors).map(([key, value]) => {
              const Icon = connectorIcons[key as keyof typeof connectorIcons] || CheckCircle2;
              return (
                <div key={key} className="flex items-center justify-between gap-2 text-sm">
                  <span className="flex min-w-0 items-center gap-2 text-slate-700">
                    <Icon className="size-4 shrink-0" />
                    <span className="truncate">{key.replace("_", " ")}</span>
                  </span>
                  <span
                    className={cn(
                      "rounded-md px-2 py-1 text-xs font-medium",
                      value.available ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                    )}
                  >
                    {value.available ? "ready" : "setup"}
                  </span>
                </div>
              );
            })}
        </div>
      </section>
    </aside>
  );
}

const inputClass =
  "min-h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 shadow-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100";

const textareaClass =
  "w-full resize-y rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 shadow-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-1">
      <span className="text-xs font-semibold text-slate-600">{label}</span>
      {children}
    </label>
  );
}

function toForm(profile: Profile | null): ProfileForm {
  return {
    name: profile?.name || "Amisha Negi",
    currentRole: profile?.current_role || "SDE-2",
    experienceYears: String(profile?.experience_years ?? 4),
    skills: (profile?.skills || []).join(", "),
    preferredRoles: (profile?.preferred_roles || []).join(", "),
    preferredLocations: (profile?.preferred_locations || []).join(", "),
  };
}

function parseList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}
