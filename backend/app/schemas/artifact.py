from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    kind: str
    content: str
    file_path: str | None
    created_at: datetime


class GenerateArtifactsResponse(BaseModel):
    artifacts: list[ArtifactRead]

