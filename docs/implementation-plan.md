# Career Pivot Implementation Plan

## Objective

Build a local-first AI job-search agent for Amisha Negi that parses a resume, discovers software engineering jobs, scores them against the target profile, generates tailored application material, assists with browser-based application forms, supports recruiter outreach, and tracks the complete funnel in a dashboard.

## Profile Baseline

- Name: Amisha Negi
- Experience: 4+ years
- Current role: SDE-2
- Core skills: Python, Django, AngularJS, Elasticsearch, Redis, MySQL, Celery, AWS
- Target roles: Senior Software Engineer, Backend Engineer, Software Engineer, Full Stack Engineer, SDE-2
- Target locations: Remote India, Delhi NCR, Bangalore, Hyderabad, Pune
- Minimum match score: 80

## Phase 1: Foundation

- Create a Dockerized monorepo with FastAPI backend, React frontend, PostgreSQL, and shared data folders.
- Define the database schema for profiles, jobs, applications, artifacts, recruiter outreach, and run logs.
- Add environment templates and setup scripts.
- Add API health checks and test scaffolding.

## Phase 2: Resume Intelligence

- Parse the resume PDF from `data/resumes/Amisha_Resume.pdf`.
- Extract profile JSON: skills, experience, companies, projects, education, and keywords.
- Store the canonical profile in PostgreSQL.
- Allow profile preference edits through API and dashboard.

## Phase 3: Job Discovery

- Implement source adapters:
  - Greenhouse public board API
  - Lever public postings API
  - Generic company career pages
  - Playwright-assisted public/job-board adapters for LinkedIn, Wellfound, Instahyre, Naukri, and Indeed
  - Sample source for local development and tests
- Run discovery manually from the API/dashboard.
- Run discovery every morning through APScheduler in the backend.
- Dedupe jobs by source/external ID and URL.

## Phase 4: Scoring Engine

- Score every job from 0 to 100.
- Weight skill overlap, experience, location, seniority, and tech relevance.
- Persist score breakdowns for explainability.
- Mark jobs below the configured threshold as skipped with a rejection reason.

## Phase 5: Application Assistant

- Generate tailored resume content, cover letter, recruiter message, and common application answers.
- Use OpenAI APIs when `OPENAI_API_KEY` is present.
- Fall back to deterministic local templates when the API key is not configured.
- Create application records and generated artifacts before submission.

## Phase 6: Browser Automation

- Use Playwright to open job application pages, fill common fields, upload the resume, and stop before final submit by default.
- Enable true auto-submit only with explicit environment flags.
- Persist browser storage state under `playwright/.auth/` for user-managed logged-in sessions.

## Phase 7: Recruiter Outreach

- Extract recruiter contacts from job descriptions when present.
- Generate personalized recruiter messages.
- Send email through SMTP/Gmail app-password configuration when enabled.
- Keep dry-run mode on by default and track outreach status.

## Phase 8: Dashboard

- Build a React dashboard with New Jobs, Applied, Interviewing, Rejected, Offers, and Follow-ups.
- Show score breakdowns, generated artifacts, source links, outreach status, and run logs.
- Provide controls for discovery, artifact generation, status updates, and outreach.

## Phase 9: Integrations

- Gmail: SMTP/Gmail app password in the runnable app; Codex Gmail connector is available in this current workspace for assistant-side operations.
- Google Sheets: optional service-account export adapter.
- Browser automation: Playwright.
- Calendar: optional Google Calendar adapter placeholder.
- LinkedIn: Playwright-assisted browser flow; no first-class LinkedIn MCP connector is exposed in this session.

## Phase 10: Verification And Deployment

- Add unit tests for resume extraction, scoring, discovery normalization, and API routes.
- Add Docker Compose deployment.
- Document workflows for setup, importing resume, discovering jobs, generating materials, pre-filling applications, and sending outreach.
