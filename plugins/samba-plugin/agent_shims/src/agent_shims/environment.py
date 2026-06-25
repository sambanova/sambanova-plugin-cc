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

    Lets SambaManaged / Stack customers point the plugin at their own
    (OpenAI-compatible) deployment. Resolution order:

      1. SAMBANOVA_BASE_URL      (preferred, customer-facing name)
      2. SAMBANOVA_API_OVERRIDE  (legacy name, still honored for back-compat)
      3. DEFAULT_SAMBANOVA_BASE_URL (public SambaNova Cloud)

    The value is normalized so callers can safely append paths like "/models":
    any trailing slash is stripped, and a trailing "/chat/completions" is
    removed too — so a customer who pastes a full endpoint URL
    (e.g. "https://api.example.ai/v1/chat/completions") still gets the correct
    base ("https://api.example.ai/v1").
    """
    raw = (
        os.environ.get("SAMBANOVA_BASE_URL")
        or os.environ.get("SAMBANOVA_API_OVERRIDE")  # back-compat
        or DEFAULT_SAMBANOVA_BASE_URL
    )
    url = raw.rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")].rstrip("/")
    return url
