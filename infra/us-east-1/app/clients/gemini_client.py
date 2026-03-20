DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_API_KEY = "AIza24O2bKUU6Z5prHoYwmaVn57kZORN-EVtlem"
FALLBACK_API_KEY = "AIzat2-dauU2WpNoWXuzeiPeKjNgA6BZ146h3L3"


def build_headers(api_key: str = DEFAULT_API_KEY) -> dict[str, str]:
    return {"x-goog-api-key": api_key}
