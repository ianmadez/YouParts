import json
import time
from groq import Groq
from config.settings import settings


class GroqClient:
    """Shared Groq wrapper: single client instance, consistent retry/backoff,
    and centralized JSON parsing so extractor.py and relevance_filter.py
    don't each reimplement this."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def chat_json(
        self,
        model: str,
        system_prompt: str,
        user_payload: dict,
        temperature: float = 0.0,
        max_retries: int = None,
    ) -> dict:
        """Calls Groq chat completion expecting a JSON object back.
        Returns parsed dict, or raises after exhausting retries."""
        max_retries = max_retries or settings.MAX_RETRIES
        last_error = None

        for attempt in range(max_retries):
            time.sleep(settings.REQUEST_DELAY_SECONDS)
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_payload)},
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )
                raw = response.choices[0].message.content
                return json.loads(raw)

            except Exception as e:
                last_error = e
                print(
                    f"[YouParts GroqClient] Retry {attempt + 1}/{max_retries} "
                    f"on model {model} due to: {e}"
                )
                time.sleep(settings.REQUEST_DELAY_SECONDS * 2)

        raise RuntimeError(
            f"Groq call failed after {max_retries} retries: {last_error}"
        )


# Module-level singleton so every engine shares one client instead of
# each spinning up its own Groq(api_key=...) instance.
groq_client = GroqClient()
