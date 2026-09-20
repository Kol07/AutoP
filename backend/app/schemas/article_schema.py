from pydantic import BaseModel

class ArticleCreate:
    processingBatchID: str
    title: str
    content: str
    source: str
    published_at: str

class ArticleEmbedRequest(BaseModel):
    text:str
    
