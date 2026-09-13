from pydantic import BaseModel

class ArticleEmbedRequest(BaseModel):
    text:str