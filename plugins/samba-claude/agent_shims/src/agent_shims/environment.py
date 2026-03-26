import os

def get_sambanova_key():
    """Retrieve the SambaNova API key from environment variables."""
    key = os.environ.get("SAMBA_CLAUDE_API_KEY") or os.environ.get("SAMBANOVA_API_KEY")
    if not key:
        raise EnvironmentError(
            "SambaNova API key not found. Please set either "
            "SAMBA_CLAUDE_API_KEY or SAMBANOVA_API_KEY in your environment."
        )
    return key
