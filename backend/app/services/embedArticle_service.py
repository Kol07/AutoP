import os
from fastapi import Request

VLLM_EMBED_URL = os.getenv("VLLM_EMBED_URL","http://192.168.2.2:7000") # fallback to testing server
VLLM_EMBED_MODEL = os.getenv("VLLM_EMBED_MODEL","/models/qwen3-embedding-4b")


async def embed_text(request: Request, text: str) -> list[float]:
    
    client = request.app.state.http_client
    
    response = await client.post(
        f"{VLLM_EMBED_URL}/v1/embeddings",
        json={
            "input": text,
            "model": VLLM_EMBED_MODEL,
        },
    )

    response.raise_for_status()

    data = response.json()

    return data["data"][0]["embedding"]