export type Stage = 'ingest' | 'review' | 'compile'

export type RunStatus = 'idle' | 'running' | 'complete' | 'failed'
export type TaskStatus = 'queued' | 'running' | 'complete' | 'failed'
export type ReviewDecision = 'pending' | 'relevant' | 'irrelevant'
export type RelevanceResult = 'relevant' | 'irrelevant'
export type ProcessingStatus = 'processing' | 'pending_review' | 'reviewed' | 'failed'

export interface ArticleInput {
  recordTitle: string
  recordContent: string
  recordSourceName?: string
  recordISOTimeStamp?: string
}

export interface SimilarityMatch {
  id: string
  title: string
  source: string
  score: number
  relevanceResult: RelevanceResult
}

export interface GuidelineHit {
  id: string
  reason: string
}

export interface WorkflowTask {
  status: TaskStatus
}

export interface Article {
  id: string
  sequence: number
  title: string
  content: string
  source: string
  publishedAt?: string
  wordCount: number
  confidence?: number
  systemPrediction?: RelevanceResult
  reviewDecision: ReviewDecision
  reviewerNote: string
  guidelineHits: GuidelineHit[]
  motherhoodResult?: RelevanceResult
  motherhoodReason: string
  similarityMatches: SimilarityMatch[]
  classificationReady: boolean
  embeddingModel?: string
  llmModel?: string
  workflows: {
    embedding: WorkflowTask
    similarity: WorkflowTask
    llm: WorkflowTask
  }
}

export interface ProcessingBatchSummary {
  id: string
  fileName: string
  status: ProcessingStatus
  totalArticles: number
  processedArticles: number
  createdAt: string
  completedAt: string | null
}

export interface BatchReview {
  decision: RelevanceResult
  remarks: string | null
  reviewedBy: string
  reviewedAt: string
}

export interface BatchClassification {
  id: string
  status: ProcessingStatus
  guidelineResult: RelevanceResult
  guidelineReason: string | null
  guidelineHits: Array<{ guidelineID: string; reason: string }>
  motherhoodResult: RelevanceResult
  motherhoodReason: string | null
  similarityResult: RelevanceResult | null
  confidenceScore: number | null
  systemPrediction: RelevanceResult | null
  llmModel: string
  embeddingModel: string
  similarityMatches: Array<{
    articleID: string
    title: string
    source: string | null
    similarityScore: number
    relevanceResult: RelevanceResult
  }>
  review: BatchReview | null
}

export interface BatchArticle {
  id: string
  sequence: number
  title: string
  content: string
  source: string | null
  publishedAt: string | null
  wordCount: number
  embeddingComplete: boolean
  classification: BatchClassification | null
}

export interface ProcessingBatch extends ProcessingBatchSummary {
  articles: BatchArticle[]
}

export interface Compilation {
  id: string
  title: string
  introduction: string
  articleIds: string[]
  previewMode: 'lead' | 'full'
  createdAt: string
  updatedAt: string
}
