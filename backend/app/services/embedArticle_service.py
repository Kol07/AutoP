import os
import httpx

VLLM_EMBED_URL = os.getenv("VLLM_EMBED_URL")

async def embed_text(text: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VLLM_EMBED_URL}/v1/embeddings",
            json={
                "input": text,
                "model": "/models/qwen3-embedding-4b",
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["data"][0]["embedding"]