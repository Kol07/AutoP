import type { Article, ProcessingBatch, TaskStatus } from '../types'

function taskStatus(complete: boolean, batchFailed: boolean): TaskStatus {
  if (complete) return 'complete'
  return batchFailed ? 'failed' : 'queued'
}

export function mapBatchArticles(batch: ProcessingBatch): Article[] {
  const batchFailed = batch.status === 'failed'

  return batch.articles.map((article) => {
    const classification = article.classification
    return {
      id: article.id,
      sequence: article.sequence,
      title: article.title,
      content: article.content,
      source: article.source?.trim() || 'Unknown source',
      publishedAt: article.publishedAt ?? undefined,
      wordCount: article.wordCount,
      confidence: classification?.confidenceScore ?? undefined,
      systemPrediction: classification?.systemPrediction ?? undefined,
      reviewDecision: classification?.review?.decision ?? 'pending',
      reviewerNote: classification?.review?.remarks ?? '',
      guidelineHits: classification?.guidelineHits.map((hit) => ({
        id: hit.guidelineID,
        reason: hit.reason,
      })) ?? [],
      motherhoodResult: classification?.motherhoodResult ?? undefined,
      motherhoodReason: classification?.motherhoodReason ?? '',
      similarityMatches: classification?.similarityMatches.map((match) => ({
        id: match.articleID,
        title: match.title,
        source: match.source?.trim() || 'Unknown source',
        score: match.similarityScore,
        relevanceResult: match.relevanceResult,
      })) ?? [],
      classificationReady: Boolean(classification),
      embeddingModel: classification?.embeddingModel,
      llmModel: classification?.llmModel,
      workflows: {
        embedding: { status: taskStatus(article.embeddingComplete, batchFailed) },
        similarity: { status: taskStatus(Boolean(classification), batchFailed) },
        llm: { status: taskStatus(Boolean(classification), batchFailed) },
      },
    }
  })
}
