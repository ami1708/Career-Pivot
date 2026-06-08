from app.services.job_sources.sample import SampleSource
from app.services.job_sources.public_apis import RemoteOKSource, RemotiveSource


def test_sample_source_returns_normalized_jobs() -> None:
    jobs = SampleSource().fetch("Backend Engineer", "Remote India", limit=2)

    assert jobs
    assert jobs[0].skills
    assert jobs[0].seniority
    assert jobs[0].url.startswith("https://")


def test_remotive_source_parses_jobs(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "jobs": [
                    {
                        "id": 123,
                        "url": "https://remotive.com/jobs/123",
                        "title": "Backend Engineer",
                        "company_name": "Acme",
                        "candidate_required_location": "India",
                        "description": "<p>Python Django Redis AWS</p>",
                        "job_type": "full_time",
                    }
                ]
            }

    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: Response())

    jobs = RemotiveSource().fetch("Backend Engineer", "Remote India", limit=5)

    assert len(jobs) == 1
    assert jobs[0].company == "Acme"
    assert "Python" in jobs[0].skills


def test_remoteok_source_parses_jobs(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> list:
            return [
                {"legal": "ok"},
                {
                    "id": 456,
                    "url": "https://remoteok.com/remote-jobs/456",
                    "position": "Python Backend Engineer",
                    "company": "RemoteCo",
                    "location": "Worldwide",
                    "description": "Python Django MySQL Redis",
                    "tags": ["python", "django"],
                },
            ]

    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: Response())

    jobs = RemoteOKSource().fetch("Backend Engineer", "Remote India", limit=5)

    assert len(jobs) == 1
    assert jobs[0].company == "RemoteCo"
    assert "Django" in jobs[0].skills
