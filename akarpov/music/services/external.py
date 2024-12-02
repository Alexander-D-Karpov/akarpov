from functools import wraps
from typing import Any

import requests
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


class ExternalServiceClient:
    def __init__(self):
        self.base_url = getattr(settings, "MUSIC_EXTERNAL_SERVICE_URL", None)

    def _make_request(
        self, endpoint: str, params: dict = None, **kwargs
    ) -> dict | None:
        if not self.base_url:
            return None

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(url, params=params, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                "External service request failed",
                error=str(e),
                endpoint=endpoint,
                params=params,
            )
            return None

    def get_spotify_info(self, track_name: str) -> dict[str, Any] | None:
        return self._make_request("/spotify/search", params={"query": track_name})

    def translate_text(
        self, text: str, source_lang: str = "auto", target_lang: str = "en"
    ) -> str | None:
        response = self._make_request(
            "/translation/translate",
            json={"text": text, "source_lang": source_lang, "target_lang": target_lang},
        )
        return response.get("translated_text") if response else None


def external_service_fallback(fallback_func):
    """Decorator to try external service first, then fall back to local implementation"""

    @wraps(fallback_func)
    def wrapper(*args, **kwargs):
        if (
            not hasattr(settings, "MUSIC_EXTERNAL_SERVICE_URL")
            or not settings.MUSIC_EXTERNAL_SERVICE_URL
        ):
            return fallback_func(*args, **kwargs)

        client = ExternalServiceClient()
        try:
            if fallback_func.__name__ == "get_spotify_info":
                result = client.get_spotify_info(args[1])  # args[1] is track_name
            elif fallback_func.__name__ == "safe_translate":
                result = client.translate_text(args[0])  # args[0] is text

            if result:
                return result
        except Exception as e:
            logger.error(
                "External service failed, falling back to local implementation",
                error=str(e),
                function=fallback_func.__name__,
            )

        return fallback_func(*args, **kwargs)

    return wrapper
