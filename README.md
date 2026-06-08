# Career Pivot

Local-first AI job-search agent for Amisha Negi. It parses a resume, maintains a structured profile, discovers jobs, scores matches, generates tailored application material, prepares and auto-applies to eligible jobs, drafts recruiter outreach, and tracks the funnel in a React dashboard.

## What Is Included

- FastAPI backend with PostgreSQL-ready SQLAlchemy models.
- React + Vite dashboard for New Jobs, Applied, Interviewing, Rejected, Offers, Follow-ups, and Skipped.
- Resume PDF parser with structured JSON extraction.
- Job discovery adapters for live public job APIs, Greenhouse, Lever, generic company career pages, sample jobs, and Playwright-assisted job boards.
- Explainable 0-100 scoring engine with the default minimum score set to 80.
- Auto-apply eligibility gates for matched skills, salary bracket, experience level, and preferred locations.
- Big-company preference ranking for eligible auto-apply jobs.
- OpenAI-powered resume tailoring, cover letters, recruiter messages, and application answers.
- Local template fallback when `OPENAI_API_KEY` is not configured.
- SMTP/Gmail outreach adapter with dry-run enabled by default.
- Auto-apply runner that processes high-score jobs, prepares missing material, and uses Playwright for supported forms when live submission is explicitly enabled.
- Docker Compose deployment, schema docs, setup scripts, tests, and example workflows.

## Quick Start

```bash
cd /Users/amishanegi/ai-job-search-agent
cp .env.example .env
./scripts/setup.sh
docker compose up --build
```

Open the dashboard at `http://localhost:5173`.

The backend API runs at `http://localhost:8000/api`.

## First Workflow

1. Put your resume at `data/resumes/Amisha_Resume.pdf` or use the one already copied from `/Users/amishanegi/Amisha_Resume.pdf`.
2. Start Docker Compose.
3. Click `Import Resume`.
4. Click `Run Discovery`.
5. Select a high-scoring job.
6. Click `Generate Material`.
7. Click `Prepare Application`.
8. Click `Auto Apply` to process high-scoring new jobs.
9. Click `Draft or Send Outreach`.

By default, application submission and outreach are dry-run. This is intentional. Set the environment flags only after you have reviewed the generated material and configured credentials.

## Environment

Important values in `.env`:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
MIN_MATCH_SCORE=80
PREFERRED_SALARY_MIN_LPA=
PREFERRED_SALARY_MAX_LPA=
AUTO_APPLY_REQUIRE_SALARY=true
AUTO_APPLY_MIN_MATCHED_SKILLS=3
BIG_COMPANY_NAMES=airbnb,stripe,databricks,mongodb,hashicorp,postman,vercel,netlify
RUN_SCHEDULER=true
DAILY_DISCOVERY_HOUR=8
DAILY_DISCOVERY_MINUTE=0
DAILY_AUTO_APPLY_ENABLED=true
DAILY_AUTO_APPLY_LIMIT=10

GREENHOUSE_COMPANIES=
LEVER_COMPANIES=
COMPANY_CAREER_URLS=
PUBLIC_JOB_APIS_ENABLED=true
BROWSER_JOB_BOARDS_ENABLED=false

APPLICATION_DRY_RUN=true
REQUIRE_APPLICATION_APPROVAL=true
AUTO_APPLY_ENABLED=false

OUTREACH_DRY_RUN=true
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
```

## Discovery Sources

By default, discovery uses public job APIs plus a small default set of Greenhouse/Lever company boards. Greenhouse and Lever are reliable because they expose public job APIs. Add company slugs:

```bash
GREENHOUSE_COMPANIES=stripe,airbnb
LEVER_COMPANIES=netlify,postman
```

Generic career pages can be added as comma-separated URLs:

```bash
COMPANY_CAREER_URLS=https://example.com/careers,https://example.org/jobs
```

LinkedIn, Wellfound, Instahyre, Naukri, and Indeed are supported through Playwright-assisted browser flows only when explicitly enabled or selected. These sites can require login, captchas, or have changing markup. The project keeps those adapters conservative and configurable rather than bypassing platform controls.

## Morning Automation

`RUN_SCHEDULER=true` starts APScheduler inside the backend and runs discovery every day at the configured hour/minute in `SCHEDULER_TIMEZONE`.

For system-level scheduling, run:

```bash
docker compose up -d
```

The backend process will keep the daily job active.

## API Examples

```bash
curl -X POST http://localhost:8000/api/profile/resume/import-local
curl -X POST http://localhost:8000/api/jobs/discover -H 'Content-Type: application/json' -d '{"limit": 60}'
curl http://localhost:8000/api/jobs?min_score=80
curl -X POST http://localhost:8000/api/jobs/1/generate-artifacts
curl -X POST http://localhost:8000/api/jobs/1/apply/prepare
curl -X POST http://localhost:8000/api/applications/auto-apply -H 'Content-Type: application/json' -d '{"limit": 10}'
```

## Docs

- [Implementation Plan](docs/implementation-plan.md)
- [Architecture](docs/architecture.md)
- [Database Schema](docs/schema.sql)
- [Example Workflows](examples/workflows.md)

## Tests

```bash
cd backend
python -m pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

## Safety Notes

- The agent rejects jobs below 80 by setting them to `skipped`.
- Auto Apply requires role/location fit, minimum matched skills, experience fit, and salary fit before submission.
- Salary checks use INR LPA. If `AUTO_APPLY_REQUIRE_SALARY=true`, jobs without listed salary are skipped.
- Eligible jobs at larger companies are attempted first using `BIG_COMPANY_NAMES` plus built-in large-company heuristics.
- Outreach is dry-run unless SMTP credentials are configured and `OUTREACH_DRY_RUN=false`.
- Auto Apply prepares applications in safe mode by default. Real submission requires `AUTO_APPLY_ENABLED=true`, `APPLICATION_DRY_RUN=false`, and `REQUIRE_APPLICATION_APPROVAL=false`.
- Browser automation does not bypass captchas, paywalls, or login controls.
