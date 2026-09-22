from pydantic import BaseModel
from datetime import datetime

class ArticleIngest(BaseModel):
    recordTitle: str
    recordContent: str
    recordSourceName: str | None = None
    recordISOTimeStamp: datetime | None = None

class ArticleCreate(BaseModel):
    processingBatchID: str
    title: str
    content: str
    source: str | None = None
    published_at: datetime | None = None

class ArticleEmbedRequest(BaseModel):
    text:str

class ArticleEmbeddingsCreate(BaseModel):
    articleID: str
    modelName: str
    modelRevision: str
    embedding: list[float]
    embeddingDimension: int
    
