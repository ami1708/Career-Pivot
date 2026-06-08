import re
import html


KNOWN_TECH = {
    "python",
    "django",
    "fastapi",
    "flask",
    "angularjs",
    "angular",
    "react",
    "typescript",
    "javascript",
    "elasticsearch",
    "redis",
    "mysql",
    "postgresql",
    "postgres",
    "celery",
    "aws",
    "lambda",
    "sqs",
    "sns",
    "docker",
    "kubernetes",
    "microservices",
    "rest",
    "graphql",
    "sql",
    "nosql",
    "mongodb",
    "rabbitmq",
    "kafka",
    "airflow",
    "ci/cd",
}

ROLE_SENIORITY = {
    "intern": "intern",
    "junior": "junior",
    "associate": "junior",
    "software engineer": "mid",
    "sde-1": "mid",
    "sde 1": "mid",
    "sde-2": "mid-senior",
    "sde 2": "mid-senior",
    "backend engineer": "mid-senior",
    "full stack engineer": "mid-senior",
    "senior": "senior",
    "staff": "staff",
    "principal": "principal",
    "lead": "lead",
}


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9+#./-]+", " ", value.lower()).strip()


def extract_skills(text: str, known: set[str] | None = None) -> list[str]:
    haystack = f" {normalize_token(text)} "
    skills = known or KNOWN_TECH
    found = []
    for skill in sorted(skills):
        needle = f" {normalize_token(skill)} "
        if needle in haystack or normalize_token(skill).replace(" ", "") in haystack.replace(" ", ""):
            found.append(skill)
    return canonicalize_skills(found)


def canonicalize_skills(skills: list[str]) -> list[str]:
    canonical = {
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "angularjs": "AngularJS",
        "fastapi": "FastAPI",
        "ci/cd": "CI/CD",
        "aws": "AWS",
        "mysql": "MySQL",
        "redis": "Redis",
        "django": "Django",
        "python": "Python",
        "celery": "Celery",
        "elasticsearch": "Elasticsearch",
    }
    result = []
    seen = set()
    for skill in skills:
        key = normalize_token(skill)
        value = canonical.get(key, skill.strip())
        if value and value.lower() not in seen:
            seen.add(value.lower())
            result.append(value)
    return result


def infer_seniority(title: str) -> str:
    normalized = normalize_token(title)
    for marker, seniority in ROLE_SENIORITY.items():
        if marker in normalized:
            return seniority
    return "mid"


def extract_email(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    return match.group(0) if match else None


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_html(value: str) -> str:
    text = html.unescape(value)
    text = text.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    while "<" in text and ">" in text:
        start = text.find("<")
        end = text.find(">", start)
        if end == -1:
            break
        text = text[:start] + " " + text[end + 1 :]
    return html.unescape(text)
