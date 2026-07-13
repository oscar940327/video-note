from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path | None = None) -> None:
    """Load a small .env file without overriding real environment variables."""
    env_path = path or ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_base_url: str
    openrouter_site_url: str
    openrouter_app_title: str
    max_llm_context_chars: int
    vault_path: Path | None = None
    vault_auto_create_folders: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        vault_value = os.getenv("VIDEONOTE_VAULT_PATH", "").strip()
        return cls(
            data_dir=Path(os.getenv("VIDEONOTE_DATA_DIR", ROOT_DIR / "data")).resolve(),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
            openrouter_model=os.getenv("OPENROUTER_MODEL", "~google/gemini-flash-latest"),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
            openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", "http://127.0.0.1:4173"),
            openrouter_app_title=os.getenv("OPENROUTER_APP_TITLE", "VideoNote Forge"),
            max_llm_context_chars=int(os.getenv("MAX_LLM_CONTEXT_CHARS", "120000")),
            vault_path=Path(vault_value).resolve() if vault_value else None,
            vault_auto_create_folders=os.getenv("VIDEONOTE_VAULT_AUTO_CREATE_FOLDERS", "true").lower()
            in {"1", "true", "yes", "on"},
        )


settings = Settings.from_env()
