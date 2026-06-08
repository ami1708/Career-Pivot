CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    current_role VARCHAR(255),
    experience_years FLOAT NOT NULL DEFAULT 0,
    skills JSON NOT NULL DEFAULT '[]',
    preferred_roles JSON NOT NULL DEFAULT '[]',
    preferred_locations JSON NOT NULL DEFAULT '[]',
    resume_text TEXT,
    profile_json JSON NOT NULL DEFAULT '{}',
    source_resume_path TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    external_id VARCHAR(255),
    url TEXT NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    remote BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    requirements JSON NOT NULL DEFAULT '[]',
    skills JSON NOT NULL DEFAULT '[]',
    seniority VARCHAR(100),
    employment_type VARCHAR(100),
    score INTEGER NOT NULL DEFAULT 0,
    score_breakdown JSON NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'new',
    rejection_reason TEXT,
    recruiter_name VARCHAR(255),
    recruiter_email VARCHAR(255),
    raw JSON NOT NULL DEFAULT '{}',
    discovered_at TIMESTAMP NOT NULL,
    applied_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE artifacts (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    kind VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'prepared',
    answers JSON NOT NULL DEFAULT '{}',
    resume_artifact_id INTEGER REFERENCES artifacts(id),
    cover_letter_artifact_id INTEGER REFERENCES artifacts(id),
    submitted_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE outreach (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    recruiter_name VARCHAR(255),
    recruiter_email VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    sent_at TIMESTAMP,
    last_follow_up_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE run_logs (
    id SERIAL PRIMARY KEY,
    kind VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    summary JSON NOT NULL DEFAULT '{}',
    error TEXT
);

