"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load backend/.env regardless of process cwd (uvicorn may be started from repo root).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fpl_base_url: str = "https://fantasy.premierleague.com/api"
    database_url: str = "sqlite:///./fpl_comanager.db"

    # GMI Cloud — inference HTTP API (Kimi runs here via model id)
    gmi_api_key: str = "placeholder"
    gmi_base_url: str = "https://api.gmi-serving.com/v1"
    gmi_organization_id: str = ""

    # Kimi model ids as registered on GMI (not separate Kimi API keys)
    kimi_model: str = "kimi-k2-5"
    kimi_vision_model: str = "kimi-k2-5"

    # Dify — workflow orchestration (POST /workflows/run); not used for explanations
    dify_api_key: str = "placeholder"
    dify_base_url: str = "https://api.dify.ai/v1"
    dify_timeout_seconds: float = 120.0
    dify_input_squad: str = "squad"
    dify_input_recommendation: str = "recommendation"
    dify_input_deterministic: str = "deterministic_explanation"
    dify_input_user_id: str = "user_id"
    # Optional: START variable name; when non-empty, backend also sends one paragraph with all four sections (easier than four `/` inserts).
    dify_input_bundle: str = ""

    # HydraDB — persistent memory API
    hydradb_api_key: str = "placeholder"
    hydradb_base_url: str = "https://api.hydradb.com"
    hydradb_tenant_id: str = ""
    hydradb_infer_on_write: bool = False
    hydradb_max_results: int = 15

    hydra_database_url: str = "placeholder"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @model_validator(mode="after")
    def normalize_dify_start_variable_names(self) -> "Settings":
        """Strip whitespace from DIFY_INPUT_* so API keys match Dify START node names exactly."""
        pairs: list[tuple[str, str]] = [
            ("dify_input_squad", "squad"),
            ("dify_input_recommendation", "recommendation"),
            ("dify_input_deterministic", "deterministic_explanation"),
            ("dify_input_user_id", "user_id"),
        ]
        for attr, default in pairs:
            raw = getattr(self, attr, "") or ""
            cleaned = raw.strip() if isinstance(raw, str) else str(raw).strip()
            setattr(self, attr, cleaned or default)
        bundle = getattr(self, "dify_input_bundle", "") or ""
        setattr(
            self,
            "dify_input_bundle",
            bundle.strip() if isinstance(bundle, str) else str(bundle).strip(),
        )
        return self


def get_settings() -> Settings:
    """New Settings each call so .env edits apply after server restart (no stale lru_cache)."""
    return Settings()
