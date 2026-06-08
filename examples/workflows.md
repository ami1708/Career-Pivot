# Example Workflows

## Daily Job Search

1. Backend scheduler wakes up at 8:00 Asia/Kolkata.
2. Discovery adapters fetch jobs from configured sources.
3. Jobs are normalized and deduped by URL/source ID.
4. The scoring engine evaluates each job against Amisha's profile.
5. Jobs scoring 80 or above stay in `new`.
6. Jobs below 80 move to `skipped` with a rejection reason.

## Manual Discovery

```bash
curl -X POST http://localhost:8000/api/jobs/discover \
  -H 'Content-Type: application/json' \
  -d '{"sources": ["greenhouse", "lever", "sample"], "limit": 50}'
```

## Resume Import

```bash
curl -X POST http://localhost:8000/api/profile/resume/import-local
```

This parses `data/resumes/Amisha_Resume.pdf` and updates the structured profile.

## Generate Application Material

```bash
curl -X POST http://localhost:8000/api/jobs/1/generate-artifacts
```

Generated files are written to:

```text
data/generated/job-1/
```

## Prepare Application

```bash
curl -X POST http://localhost:8000/api/jobs/1/apply/prepare
```

The agent creates an application record, links generated resume/cover-letter artifacts, and stores common answer payloads.

## Auto Apply

```bash
curl -X POST http://localhost:8000/api/applications/auto-apply \
  -H 'Content-Type: application/json' \
  -d '{"limit": 10}'
```

The runner processes high-scoring `new` jobs, checks matched skills, salary bracket, experience level, and location, then ranks eligible jobs with a preference for larger companies. It generates missing application material, prepares an application record, and submits only when live submission is explicitly enabled. In the default safe mode it stops after preparation and records the result.

Salary bracket is configured in INR LPA:

```bash
PREFERRED_SALARY_MIN_LPA=25
PREFERRED_SALARY_MAX_LPA=45
AUTO_APPLY_REQUIRE_SALARY=true
AUTO_APPLY_MIN_MATCHED_SKILLS=3
```

## Recruiter Outreach

```bash
curl -X POST http://localhost:8000/api/jobs/1/outreach/send
```

If a recruiter email is available and SMTP is configured, the email can be sent. Otherwise it is stored as a draft/dry-run.

## Funnel Tracking

```bash
curl -X PATCH http://localhost:8000/api/jobs/1/status \
  -H 'Content-Type: application/json' \
  -d '{"status": "interviewing"}'
```

Supported statuses:

- `new`
- `applied`
- `interviewing`
- `rejected`
- `offers`
- `follow_up`
- `skipped`
