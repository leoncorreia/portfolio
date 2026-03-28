"""Helpers to detect whether integration env vars are real vs placeholders."""


def is_live_key(value: str | None) -> bool:
    if not value:
        return False
    # Strip quotes/BOM often pasted from docs
    v = value.strip().strip("\ufeff").strip('"').strip("'").strip().lower()
    if v in ("", "placeholder", "changeme", "your-api-key", "sk-placeholder", "app-placeholder"):
        return False
    return True
