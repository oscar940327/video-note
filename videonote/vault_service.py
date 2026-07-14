from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from .config import Settings, settings
from .llm_service import OpenRouterClient, load_prompt
from .utils import atomic_write_text, safe_name


class VaultError(RuntimeError):
    pass


CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["use_existing", "create_new", "inbox"]},
        "folder": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
    "required": ["action", "folder", "confidence", "reason"],
    "additionalProperties": False,
}


def require_vault(app_settings: Settings = settings) -> Path:
    if not app_settings.vault_path:
        raise VaultError("VIDEONOTE_VAULT_PATH is not configured.")
    root = app_settings.vault_path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def list_topic_folders(root: Path) -> list[str]:
    ignored = {".git", ".obsidian", "attachments", "private"}
    return sorted(
        item.name for item in root.iterdir()
        if item.is_dir() and item.name.lower() not in ignored and not item.name.startswith(".")
    )


def _clean_folder(value: str) -> str:
    if any(token in value for token in ("..", "/", "\\", ":")):
        raise VaultError("The proposed Vault folder is not a safe single folder name.")
    cleaned = safe_name(value, limit=60).strip()
    if not cleaned or cleaned.startswith("."):
        raise VaultError("The proposed Vault folder is empty or invalid.")
    return cleaned


def _title_from_markdown(markdown: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", markdown, re.MULTILINE)
    return safe_name(match.group(1) if match else "Untitled VideoNote", limit=120)


def classify_note(
    markdown: str,
    client: OpenRouterClient | None = None,
    app_settings: Settings = settings,
) -> dict[str, Any]:
    root = require_vault(app_settings)
    folders = list_topic_folders(root)
    result = (client or OpenRouterClient(app_settings)).structured(
        name="vault_topic_classification",
        schema=CLASSIFICATION_SCHEMA,
        instructions=load_prompt("vault_classifier.md"),
        input_text=(
            f"Existing folders: {folders or ['Inbox']}\n\n"
            f"Classify this note:\n\n{markdown[:8000]}"
        ),
        max_output_tokens=500,
        model=app_settings.classification_model,
        reasoning_enabled=False,
    )
    confidence = float(result["confidence"])
    existing = {name.casefold(): name for name in folders}
    proposed = _clean_folder(str(result["folder"]))
    action = str(result["action"])
    if confidence < 0.65 or action == "inbox":
        action, folder = "inbox", "Inbox"
    elif action == "use_existing" and proposed.casefold() in existing:
        folder = existing[proposed.casefold()]
    elif app_settings.vault_auto_create_folders:
        action, folder = "create_new", proposed
    else:
        action, folder = "inbox", "Inbox"
    return {
        "action": action,
        "folder": folder,
        "confidence": confidence,
        "reason": str(result["reason"]),
        "filename": f"{_title_from_markdown(markdown)}.md",
    }


def _safe_target(root: Path, folder: str, filename: str) -> Path:
    target = (root / _clean_folder(folder) / f"{safe_name(Path(filename).stem, limit=120)}.md").resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise VaultError("The target path escapes the configured Vault.") from error
    return target


def save_note(
    markdown: str,
    folder: str | None = None,
    relative_path: str | None = None,
    client: OpenRouterClient | None = None,
    app_settings: Settings = settings,
) -> dict[str, Any]:
    root = require_vault(app_settings)
    classification = classify_note(markdown, client, app_settings) if not folder and not relative_path else None
    if relative_path:
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise VaultError("The target path escapes the configured Vault.") from error
        if candidate.suffix.lower() != ".md":
            raise VaultError("Vault notes must use the .md extension.")
        target = candidate
    else:
        selected_folder = folder or str(classification["folder"])
        target = _safe_target(root, selected_folder, f"{_title_from_markdown(markdown)}.md")
        if target.exists() and target.read_text(encoding="utf-8") != markdown:
            stem, counter = target.stem, 2
            while target.exists():
                target = target.with_name(f"{stem}-{counter}.md")
                counter += 1
    atomic_write_text(target, markdown.rstrip() + "\n")
    return {
        "saved": True,
        "relative_path": target.relative_to(root).as_posix(),
        "absolute_path": str(target),
        "classification": classification,
    }


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=check,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or str(error)).strip()
        raise VaultError(f"Git command failed: {detail}") from error


def publish_note(
    markdown: str,
    folder: str | None = None,
    relative_path: str | None = None,
    client: OpenRouterClient | None = None,
    app_settings: Settings = settings,
) -> dict[str, Any]:
    saved = save_note(markdown, folder, relative_path, client, app_settings)
    root = require_vault(app_settings)
    top = _git(["rev-parse", "--show-toplevel"], root).stdout.strip()
    if not top:
        raise VaultError("The Vault is not inside a Git repository.")
    repo = Path(top)
    path_in_repo = Path(saved["absolute_path"]).relative_to(repo).as_posix()
    _git(["add", "--", path_in_repo], repo)
    diff = _git(["diff", "--cached", "--quiet"], repo, check=False)
    committed = diff.returncode != 0
    if committed:
        title = _title_from_markdown(markdown)
        _git(["commit", "-m", f"docs: publish {title}"], repo)
    remote = _git(["remote", "get-url", "origin"], repo, check=False)
    if remote.returncode != 0 or "jackyzha0/quartz" in remote.stdout:
        raise VaultError(
            "The note was saved and committed locally, but note-garden origin still needs your GitHub repository URL."
        )
    branch = _git(["branch", "--show-current"], repo).stdout.strip()
    pushed = _git(["push", "origin", branch], repo, check=False)
    if pushed.returncode != 0:
        raise VaultError(f"The note was committed locally but Git push failed: {pushed.stderr.strip()}")
    return {**saved, "committed": committed, "pushed": True, "branch": branch}
