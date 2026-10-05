import os
import httpx
import asyncio

from ..schemas.classification_schema import LLMClassificationResult


class ArticleLLMService:
    def __init__(self, httpClient: httpx.AsyncClient):

        self.httpClient = httpClient

        self.semaphore = asyncio.Semaphore(
            int(os.getenv("LLM_CONCURRENCY") or "10")
        )

        self.llmURL = (
            os.getenv("VLLM_LLM_URL") or "http://192.168.2.2:7001"
        )

        self.llmModel = (
            os.getenv("VLLM_LLM_MODEL") or "/models/qwen3.8-27B-FP8"
        )

    async def classify_article(self, content: str,) -> LLMClassificationResult:

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
        You are a news article relevance classifier.

        Your task is to determine whether a news article is relevant based on:
        1. The relevance guidelines.
        2. The motherhood statement.

        A "motherhood statement" is simply the name of a broad catch-all relevance criterion.
        It does NOT refer to mothers, pregnancy, childbirth, parenting, or family unless the
        statement itself explicitly mentions those topics.

        ==================================================
        RELEVANCE GUIDELINES
        ==================================================

        [G1.1.1] ANY THINK TANKS

        An article satisfies this guideline if it meaningfully mentions, discusses,
        quotes, references, or involves a think tank.

        ==================================================
        MOTHERHOOD STATEMENT
        ==================================================

        [M1] News regarding natural disasters.

        An article satisfies the motherhood statement if its main subject, or a
        substantial part of the article, concerns a natural disaster.

        Examples may include:
        - Earthquakes
        - Tsunamis
        - Floods
        - Typhoons
        - Hurricanes
        - Cyclones
        - Volcanic eruptions
        - Landslides
        - Wildfires caused by natural conditions
        - Other significant naturally occurring disasters

        ==================================================
        CLASSIFICATION INSTRUCTIONS
        ==================================================

        Evaluate the article independently against BOTH criteria above.

        GUIDELINE CHECK:
        - Determine whether the article satisfies [G1.1.1].
        - Do not treat universities, companies, government agencies, charities,
        advocacy groups, or research organisations as think tanks unless they
        are clearly identified as a think tank or function as one in the article.
        - If the guideline is not satisfied, state briefly why.

        MOTHERHOOD STATEMENT CHECK:
        - Determine whether the article satisfies [M1].
        - The natural disaster should be a meaningful subject of the article.
        - A brief or incidental mention of a natural disaster is not sufficient.
        - Do not interpret the word "motherhood" literally.
        - If the motherhood statement is not satisfied, state briefly why.

        GENERAL RULES:
        - Base the classification only on the provided article.
        - Do not invent facts that are not present in the article.
        - Do not introduce relevance criteria that are not listed above.
        - Evaluate the guideline and motherhood statement separately.
        - An article may match:
            - only the guideline,
            - only the motherhood statement,
            - both,
            - or neither.
        - Keep reasons concise and directly tied to the article content.

        ==================================================
        REQUIRED OUTPUT CONSISTENCY
        ==================================================

        - Always return the guidelineHits field.
        - guidelineResult and guidelineHits MUST agree:
            - If guidelineResult is "relevant", guidelineHits MUST contain one
              object for every matched guideline.
            - If guidelineResult is "irrelevant", guidelineHits MUST be an empty list.
        - For a [G1.1.1] match, include exactly:
            - guidelineID: "G1.1.1"
            - reason: a concise statement identifying the think tank and how it
              is meaningfully involved in the article.
        - Do not put the overall guideline summary in guidelineHits. Each hit
          must identify and justify one specific matched guideline.
        - guidelineReason should summarize the overall guideline decision, while
          guidelineHits should contain the per-guideline evidence.
        """

    def _build_article_prompt(
        self,
        content: str,
    ) -> str:
        return f"""
        ARTICLE

        {content}
        """
