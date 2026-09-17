from sqlalchemy.orm import relationship

from .Article_model import Article
from .ArticleEmbedding_model import ArticleEmbedding
from .ClassificationMatch_model import ClassificationMatch
from .ClassificationRun_model import ClassificationRun
from .Compilation_model import Compilation
from .ProcessingBatch_model import ProcessingBatch
from .Review_model import Review


# processing_batches
ProcessingBatch.articles = relationship(
    Article,
    back_populates="processing_batch",
    foreign_keys=[Article.processing_batch_id],
)

# compilations
Compilation.articles = relationship(
    Article,
    back_populates="compilation",
    foreign_keys=[Article.compilation_id],
)

# articles
Article.processing_batch = relationship(
    ProcessingBatch,
    back_populates="articles",
    foreign_keys=[Article.processing_batch_id],
)
Article.compilation = relationship(
    Compilation,
    back_populates="articles",
    foreign_keys=[Article.compilation_id],
)
Article.embeddings = relationship(
    ArticleEmbedding,
    back_populates="article",
    foreign_keys=[ArticleEmbedding.article_id],
)
Article.classification_runs = relationship(
    ClassificationRun,
    back_populates="article",
    foreign_keys=[ClassificationRun.article_id],
)
Article.classification_matches = relationship(
    ClassificationMatch,
    back_populates="matched_article",
    foreign_keys=[ClassificationMatch.matched_article_id],
)

# article_embeddings
ArticleEmbedding.article = relationship(
    Article,
    back_populates="embeddings",
    foreign_keys=[ArticleEmbedding.article_id],
)

# classification_runs
ClassificationRun.article = relationship(
    Article,
    back_populates="classification_runs",
    foreign_keys=[ClassificationRun.article_id],
)
ClassificationRun.review = relationship(
    Review,
    back_populates="classification_run",
    foreign_keys=[Review.classification_run_id],
    uselist=False,
)
ClassificationRun.matches = relationship(
    ClassificationMatch,
    back_populates="classification_run",
    foreign_keys=[ClassificationMatch.classification_run_id],
)

# reviews
Review.classification_run = relationship(
    ClassificationRun,
    back_populates="review",
    foreign_keys=[Review.classification_run_id],
    uselist=False,
)

# classification_matches
ClassificationMatch.classification_run = relationship(
    ClassificationRun,
    back_populates="matches",
    foreign_keys=[ClassificationMatch.classification_run_id],
)
ClassificationMatch.matched_article = relationship(
    Article,
    back_populates="classification_matches",
    foreign_keys=[ClassificationMatch.matched_article_id],
)
