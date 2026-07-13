from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from videonote.config import settings
from videonote.job_manager import job_manager
from videonote.llm_service import (
    LLMConfigurationError,
    LLMResponseError,
    OpenRouterClient,
)
from videonote.note_generator import regenerate_section
from videonote.note_validator import annotate_review_items, format_validation, validate_grounding
from videonote.pipeline import PipelineOptions
from videonote.vault_service import VaultError, classify_note, publish_note, save_note


app = FastAPI(title="VideoNote Forge API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:4173", "http://localhost:4173",
        "http://127.0.0.1:5500", "http://localhost:5500",
        "https://oscar940327.github.io",
    ],
    allow_origin_regex=r"https://oscar940327\.github\.io(?:/.*)?",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class CreateJobRequest(BaseModel):
    url: HttpUrl
    output_language: str = Field(default="zh-TW", pattern=r"^(zh-TW|en)$")
    whisper_model: str = Field(default="large-v3", pattern=r"^(tiny|base|small|medium|large-v3|turbo)$")
    note_style: str = Field(default="standard", pattern=r"^(concise|standard|detailed)$")
    grounding_mode: str = Field(default="assisted", pattern=r"^(strict|assisted|educational)$")
    force_cpu: bool = False
    cookies_from_browser: str | None = Field(default=None, pattern=r"^(chrome|edge|firefox|brave|opera|vivaldi)$")


class ValidateRequest(BaseModel):
    markdown: str = Field(min_length=1)
    job_id: str | None = None
    include_grounding: bool = False


class RegenerateRequest(BaseModel):
    job_id: str
    markdown: str = Field(min_length=1)
    section_heading: str = Field(min_length=1)
    instruction: str = "Improve clarity while remaining faithful to the transcript."


class VaultClassifyRequest(BaseModel):
    markdown: str = Field(min_length=1)


class VaultSaveRequest(BaseModel):
    markdown: str = Field(min_length=1)
    folder: str | None = None
    relative_path: str | None = None


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_configured": bool(settings.openrouter_api_key),
        "provider": "openrouter",
        "model": settings.openrouter_model,
        "vault_configured": bool(settings.vault_path),
        "vault_path": str(settings.vault_path) if settings.vault_path else None,
    }


@app.post("/api/jobs", status_code=202)
def create_job(request: CreateJobRequest) -> dict:
    job = job_manager.create(PipelineOptions(**request.model_dump(mode="json")))
    return job.public()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job.public()


@app.get("/api/jobs/{job_id}/result")
def get_result(job_id: str) -> dict:
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status == "failed":
        raise HTTPException(422, job.error or "Job failed")
    if job.status != "complete" or not job.result:
        raise HTTPException(409, "Job is not complete")
    return job.result


@app.post("/api/validate")
def validate(request: ValidateRequest) -> dict:
    result = format_validation(request.markdown)
    if request.include_grounding:
        if not request.job_id:
            raise HTTPException(400, "job_id is required for grounding validation")
        job = job_manager.get(request.job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        context_path = job_manager.data_dir / request.job_id / "transcript.context.txt"
        if not context_path.exists():
            raise HTTPException(409, "Transcript context is not ready")
        try:
            result["grounding"] = validate_grounding(
                OpenRouterClient(), request.markdown, context_path.read_text(encoding="utf-8")
            )
        except (LLMConfigurationError, LLMResponseError) as error:
            raise HTTPException(503, str(error)) from error
    result["annotated_markdown"] = annotate_review_items(request.markdown, result)
    return result


@app.post("/api/regenerate-section")
def regenerate(request: RegenerateRequest) -> dict:
    job = job_manager.get(request.job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    context_path = job_manager.data_dir / request.job_id / "transcript.context.txt"
    if not context_path.exists():
        raise HTTPException(409, "Transcript context is not ready")
    try:
        section = regenerate_section(
            OpenRouterClient(), request.markdown, request.section_heading,
            context_path.read_text(encoding="utf-8"), request.instruction,
        )
    except (LLMConfigurationError, LLMResponseError) as error:
        raise HTTPException(503, str(error)) from error
    return {"section_markdown": section}


@app.post("/api/vault/classify")
def classify_vault_note(request: VaultClassifyRequest) -> dict:
    try:
        return classify_note(request.markdown)
    except (VaultError, LLMConfigurationError, LLMResponseError) as error:
        raise HTTPException(503, str(error)) from error


@app.post("/api/vault/save")
def save_vault_note(request: VaultSaveRequest) -> dict:
    try:
        return save_note(request.markdown, request.folder, request.relative_path)
    except (VaultError, LLMConfigurationError, LLMResponseError, OSError) as error:
        raise HTTPException(503, str(error)) from error


@app.post("/api/vault/publish")
def publish_vault_note(request: VaultSaveRequest) -> dict:
    try:
        return publish_note(request.markdown, request.folder, request.relative_path)
    except (VaultError, LLMConfigurationError, LLMResponseError, OSError) as error:
        raise HTTPException(503, str(error)) from error


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8010, reload=True)
