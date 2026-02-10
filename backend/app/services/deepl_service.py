"""DeepL Translation Service"""
from typing import Optional
import httpx


class DeepLServiceError(Exception):
    pass


class DeepLService:
    """Service for translating text using DeepL API"""

    # Free tier uses api-free.deepl.com
    API_URL = "https://api-free.deepl.com/v2/translate"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def translate(
        self,
        text: str,
        target_lang: str = "KO",
        source_lang: str = "EN"
    ) -> str:
        """Translate text using DeepL API.

        Args:
            text: Text to translate
            target_lang: Target language code (default: KO for Korean)
            source_lang: Source language code (default: EN for English)

        Returns:
            Translated text
        """
        if not text.strip():
            return ""

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"DeepL-Auth-Key {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": [text],
                        "target_lang": target_lang,
                        "source_lang": source_lang,
                    }
                )

                if response.status_code == 403:
                    raise DeepLServiceError("Invalid API key")
                elif response.status_code == 456:
                    raise DeepLServiceError("Quota exceeded (500,000 chars/month limit)")
                elif response.status_code != 200:
                    raise DeepLServiceError(f"DeepL API error: {response.status_code}")

                result = response.json()
                translations = result.get("translations", [])

                if not translations:
                    raise DeepLServiceError("No translation returned")

                translated_text = translations[0].get("text", "")
                return translated_text

            except httpx.ConnectError:
                raise DeepLServiceError("Cannot connect to DeepL API")
            except httpx.TimeoutException:
                raise DeepLServiceError("DeepL API request timed out")

    async def check_usage(self) -> dict:
        """Check API usage statistics."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    "https://api-free.deepl.com/v2/usage",
                    headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"}
                )

                if response.status_code == 200:
                    return response.json()
                return {}
            except Exception:
                return {}


# Singleton instance
_deepl_service: Optional[DeepLService] = None


def get_deepl_service() -> Optional[DeepLService]:
    """Get DeepL service instance if API key is configured."""
    global _deepl_service
    if _deepl_service is None:
        from app.config import get_settings
        settings = get_settings()
        if settings.deepl_api_key:
            _deepl_service = DeepLService(settings.deepl_api_key)
    return _deepl_service


def init_deepl_service(api_key: str) -> DeepLService:
    """Initialize DeepL service with API key."""
    global _deepl_service
    _deepl_service = DeepLService(api_key)
    return _deepl_service
