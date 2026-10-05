import type { ArticleInput, ProcessingBatch, ProcessingBatchSummary } from '../types'
import { apiRequest } from './apiClient'

export function fetchLatestProcessingBatch(): Promise<ProcessingBatch> {
  return apiRequest<ProcessingBatch>('/processing-batches/latest')
}

export function fetchProcessingBatch(batchId: string): Promise<ProcessingBatch> {
  return apiRequest<ProcessingBatch>(`/processing-batches/${batchId}`)
}

export function createProcessingBatch(
  fileName: string,
  articles: ArticleInput[],
): Promise<ProcessingBatchSummary> {
  return apiRequest<ProcessingBatchSummary>('/processing-batches', {
    method: 'POST',
    body: JSON.stringify({ fileName, articles }),
  })
}
