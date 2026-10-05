export type Stage = 'ingest' | 'review' | 'compile'

export type RunStatus = 'idle' | 'running' | 'paused' | 'complete'
export type TaskStatus = 'queued' | 'running' | 'complete' | 'failed'
export type ReviewDecision = 'pending' | 'relevant' | 'irrelevant'

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
}

export interface GuidelineHit {
  id: string
  label: string
  confidence: number
  reason: string
}

export interface WorkflowTask {
  status: TaskStatus
  durationMs?: number
}

export interface Article {
  id: string
  sequence: number
  title: string
  content: string
  source: string
  sourceUrl?: string
  publishedAt?: string
  wordCount: number
  confidence: number
  systemPrediction: 'relevant' | 'irrelevant'
  reviewDecision: ReviewDecision
  reviewerNote: string
  guidelineHits: GuidelineHit[]
  motherhoodResult: 'relevant' | 'irrelevant'
  motherhoodReason: string
  similarityMatches: SimilarityMatch[]
  workflows: {
    embedding: WorkflowTask
    similarity: WorkflowTask
    llm: WorkflowTask
  }
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
