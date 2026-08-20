import os

DEFAULT_SAMBANOVA_BASE_URL = "https://api.sambanova.ai/v1"

def get_sambanova_key():
    """Retrieve the SambaNova API key from environment variables."""
    key = os.environ.get("SAMBA_CLAUDE_API_KEY") or os.environ.get("SAMBANOVA_API_KEY")
    if not key:
        raise EnvironmentError(
            "SambaNova API key not found. Please set either "
            "SAMBA_CLAUDE_API_KEY or SAMBANOVA_API_KEY in your environment."
        )
    return key

def get_sambanova_base_url():
    """Base URL for the SambaNova-compatible API.

    Honors SAMBANOVA_API_OVERRIDE to target a custom (OpenAI-compatible)
    endpoint; defaults to the public SambaNova Cloud endpoint. Any trailing
    slash is stripped so callers can append paths like "/models".
    """
    return os.environ.get(
        "SAMBANOVA_API_OVERRIDE", DEFAULT_SAMBANOVA_BASE_URL
    ).rstrip("/")
