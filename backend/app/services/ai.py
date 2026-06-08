import json
from typing import Any

from app.core.config import get_settings


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def available(self) -> bool:
        return bool(self.settings.openai_api_key)

    def generate_text(self, system: str, user: str) -> str:
        if not self.available():
            return self._local_fallback(user)

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        request = {
            "model": self.settings.openai_model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self.settings.openai_reasoning_effort:
            request["reasoning"] = {"effort": self.settings.openai_reasoning_effort}
        response = client.responses.create(**request)
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()
        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    chunks.append(text)
        return "\n".join(chunks).strip()

    def generate_json(self, system: str, user: str) -> dict[str, Any]:
        text = self.generate_text(system, user)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    def _local_fallback(self, user: str) -> str:
        return (
            "OpenAI is not configured, so this artifact was generated with a local template.\n\n"
            f"Context:\n{user[:2400]}"
        )


def profile_payload(profile: Any) -> dict[str, Any]:
    return {
        "name": profile.name,
        "current_role": profile.current_role,
        "experience_years": profile.experience_years,
        "skills": profile.skills,
        "preferred_roles": profile.preferred_roles,
        "preferred_locations": profile.preferred_locations,
        "profile_json": profile.profile_json,
    }


def job_payload(job: Any) -> dict[str, Any]:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "remote": job.remote,
        "description": job.description,
        "skills": job.skills,
        "score": job.score,
        "score_breakdown": job.score_breakdown,
        "url": job.url,
    }
