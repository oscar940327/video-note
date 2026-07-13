from __future__ import annotations

import json
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings
from .pipeline import PipelineOptions, run_pipeline
from .utils import write_json


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobState:
    job_id: str
    status: str = "queued"
    stage: str = "queued"
    progress: int = 0
    message: str = "Waiting to start"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    error: str | None = None
    result: dict[str, Any] | None = None

    def public(self, include_result: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_result:
            data.pop("result", None)
        return data


class JobManager:
    def __init__(self, data_dir: Path | None = None, max_workers: int = 1):
        self.data_dir = (data_dir or settings.data_dir) / "jobs"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, JobState] = {}
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="videonote")
        self._load_existing()

    def _load_existing(self) -> None:
        for state_path in self.data_dir.glob("*/job.json"):
            try:
                data = json.loads(state_path.read_text(encoding="utf-8"))
                job = JobState(**data)
                if job.status in {"queued", "running"}:
                    job.status = "failed"
                    job.stage = "failed"
                    job.error = "The backend stopped before this job completed. Please create a new job."
                    job.message = "Interrupted by backend restart"
                self.jobs[job.job_id] = job
            except (OSError, ValueError, TypeError):
                continue

    def create(self, options: PipelineOptions) -> JobState:
        job = JobState(job_id=uuid.uuid4().hex)
        with self.lock:
            self.jobs[job.job_id] = job
            self._save(job)
        self.executor.submit(self._run, job.job_id, options)
        return job

    def get(self, job_id: str) -> JobState | None:
        with self.lock:
            return self.jobs.get(job_id)

    def _save(self, job: JobState) -> None:
        write_json(self.data_dir / job.job_id / "job.json", job.public(include_result=True))

    def _update(self, job_id: str, **changes: Any) -> None:
        with self.lock:
            job = self.jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = now_iso()
            self._save(job)

    def _run(self, job_id: str, options: PipelineOptions) -> None:
        self._update(job_id, status="running", message="Starting VideoNote pipeline")
        try:
            result = run_pipeline(
                options,
                self.data_dir / job_id,
                lambda stage, progress, message: self._update(
                    job_id, status="running", stage=stage, progress=progress, message=message
                ),
            )
            self._update(job_id, status="complete", stage="complete", progress=100, message="Note is ready", result=asdict(result))
        except Exception as error:
            trace = traceback.format_exc()
            write_json(self.data_dir / job_id / "error.json", {"error": str(error), "traceback": trace})
            self._update(job_id, status="failed", stage="failed", message="VideoNote generation failed", error=str(error))


job_manager = JobManager()
