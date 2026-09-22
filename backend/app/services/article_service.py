import hashlib

from ..schemas.article_schema import ArticleCreate
from ..repositories.article_repository import ArticleRepository
from ..models.Article_model import Article

from sqlalchemy.ext.asyncio import AsyncSession

class ArticleService():
    def __init__(self, db: AsyncSession, repository: ArticleRepository):
        
        self.db = db
        self.repository = repository
        

    async def create_article(self, data: ArticleCreate) -> Article | None:
        
        hashed_content = hashlib.blake2b(data.content.encode("utf-8"),
                                         digest_size=16).hexdigest()
        
        article = Article(
            processing_batch_id = data.processingBatchID,
            title = data.title,
            content = data.content,
            source_url = data.source,
            published_at = data.published_at,
            content_hash = hashed_content
        )
        
        article = await self.repository.create(article)
        
        if article is None:
            return None
        
        await self.db.commit()
        await self.db.refresh(article)
        
        return article
