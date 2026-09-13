from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen3-Embedding-4B",
    local_dir="./models/qwen3-embedding-4b",
)