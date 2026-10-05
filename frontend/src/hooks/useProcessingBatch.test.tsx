import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ProcessingBatch } from '../types'
import { useProcessingBatch } from './useProcessingBatch'

function response(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response
}

function batch(status: ProcessingBatch['status']): ProcessingBatch {
  return {
    id: 'poll-batch',
    fileName: 'poll.json',
    status,
    totalArticles: 1,
    processedArticles: status === 'processing' ? 0 : 1,
    createdAt: '2026-10-05T08:00:00Z',
    completedAt: status === 'processing' ? null : '2026-10-05T08:01:00Z',
    articles: [],
  }
}

describe('useProcessingBatch polling', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('polls the exact batch id and stops after a terminal response', async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(batch('processing')))
      .mockResolvedValueOnce(response(batch('pending_review')))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useProcessingBatch())
    await act(async () => { await Promise.resolve(); await Promise.resolve() })
    expect(result.current.batch?.status).toBe('processing')

    await act(async () => { await vi.advanceTimersByTimeAsync(2_000) })
    expect(result.current.batch?.status).toBe('pending_review')
    expect(String(fetchMock.mock.calls[1][0])).toMatch(/\/processing-batches\/poll-batch$/)

    await act(async () => { await vi.advanceTimersByTimeAsync(4_000) })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
