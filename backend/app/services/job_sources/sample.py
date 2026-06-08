from app.services.job_sources.base import JobListing


class SampleSource:
    name = "sample"

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        listings = [
            JobListing(
                source=self.name,
                external_id="sample-backend-1",
                url="https://example.com/jobs/backend-platform-engineer",
                title="Senior Backend Engineer",
                company="ExampleCloud",
                location="Remote India",
                remote=True,
                description=(
                    "Build high-scale Python and Django services on AWS. "
                    "Work with Redis, MySQL, Celery, Elasticsearch, REST APIs, and distributed systems. "
                    "4+ years of software engineering experience required. recruiter@example.com"
                ),
                requirements=["Python", "Django", "AWS", "Redis", "MySQL", "Celery"],
                employment_type="Full-time",
            ),
            JobListing(
                source=self.name,
                external_id="sample-fullstack-1",
                url="https://example.com/jobs/full-stack-engineer",
                title="Full Stack Engineer",
                company="Northstar Labs",
                location="Bangalore",
                remote=False,
                description=(
                    "Own product features across Django APIs and AngularJS dashboards. "
                    "Experience with Elasticsearch and Redis preferred. 3+ years required."
                ),
                requirements=["Django", "AngularJS", "Elasticsearch", "Redis"],
                employment_type="Full-time",
            ),
            JobListing(
                source=self.name,
                external_id="sample-ios-1",
                url="https://example.com/jobs/ios-engineer",
                title="iOS Engineer",
                company="Unmatched Apps",
                location="Mumbai",
                remote=False,
                description="Swift, UIKit, and iOS role. 5+ years required.",
                requirements=["Swift", "iOS"],
                employment_type="Full-time",
            ),
        ]
        return [listing.normalized() for listing in listings[:limit]]

