import os
import httpx
import asyncio

from ..schemas.classification_schema import LLMClassificationResult


class ArticleLLMService:
    def __init__(self, httpClient: httpx.AsyncClient):

        self.httpClient = httpClient

        self.semaphore = asyncio.Semaphore(
            int(os.getenv("LLM_CONCURRENCY", "10"))
        )

        self.llmURL = os.getenv(
            "VLLM_LLM_URL",
            "http://192.168.2.2:7001",
        )

        self.llmModel = os.getenv(
            "VLLM_LLM_MODEL",
            "/models/qwen3.8-27B-FP8",
        )

    async def classify_article(
        self,
        content: str,
    ) -> LLMClassificationResult:

        async with self.semaphore:

            response = await self.httpClient.post(
                f"{self.llmURL}/v1/chat/completions",
                json={
                    "model": self.llmModel,

                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt(),
                        },
                        {
                            "role": "user",
                            "content": self._build_article_prompt(content),
                        },
                    ],

                    "temperature": 0.0,
                    "max_completion_tokens": 512,

                    "chat_template_kwargs": {
                        "enable_thinking": False,
                    },

                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "article_classification",
                            "strict": True,
                            "schema": LLMClassificationResult.model_json_schema(),
                        },
                    },
                },

                timeout=120.0,
            )

            response.raise_for_status()

            data = response.json()

            content = data["choices"][0]["message"]["content"]

            return LLMClassificationResult.model_validate_json(content)

    def _get_system_prompt(self) -> str:
        return """
        TODO
        """

    def _build_article_prompt(
        self,
        content: str,
    ) -> str:
        return f"""
        ARTICLE

        {content}
        """