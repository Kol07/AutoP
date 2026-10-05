import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { BatchArticle, ProcessingBatch } from './types'

const fetchMock = vi.fn<typeof fetch>()

function response(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response
}

function article(id: string, sequence: number, reviewed = false): BatchArticle {
  return {
    id,
    sequence,
    title: sequence === 1 ? 'Regulator fines Northwind Bank' : 'Helix Health reports cyber incident',
    content: 'A persisted article body with enough detail for review.',
    source: sequence === 1 ? 'Financial Times' : 'Reuters',
    publishedAt: '2026-10-05T08:00:00Z',
    wordCount: 10,
    embeddingComplete: true,
    classification: {
      id: `run-${id}`,
      status: reviewed ? 'reviewed' : 'pending_review',
      guidelineResult: 'relevant',
      guidelineReason: 'A material event was detected.',
      guidelineHits: [{ guidelineID: 'G-01', reason: 'A regulator imposed a penalty.' }],
      motherhoodResult: 'relevant',
      motherhoodReason: 'The event may affect public confidence.',
      similarityResult: 'relevant',
      confidenceScore: sequence === 1 ? 0.84 : 0.92,
      systemPrediction: 'relevant',
      llmModel: '/models/test-llm',
      embeddingModel: '/models/test-embedding',
      similarityMatches: [],
      review: reviewed ? {
        decision: 'relevant',
        remarks: 'Previously reviewed',
        reviewedBy: 'reviewer',
        reviewedAt: '2026-10-05T09:00:00Z',
      } : null,
    },
  }
}

function completedBatch(): ProcessingBatch {
  return {
    id: 'batch-1',
    fileName: 'real-batch.json',
    status: 'pending_review',
    totalArticles: 2,
    processedArticles: 2,
    createdAt: '2026-10-05T08:00:00Z',
    completedAt: '2026-10-05T08:01:00Z',
    articles: [article('article-1', 1), article('article-2', 2, true)],
  }
}

describe('AutoPOROTW API integration', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue(response(completedBatch()))
    vi.stubGlobal('fetch', fetchMock)
  })

  it('renders the latest persisted batch instead of demo articles', async () => {
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Latest batch complete' })).toBeInTheDocument()
    expect(await screen.findByText('Regulator fines Northwind Bank')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/api\/v1\/processing-batches\/latest$/), expect.any(Object))
  })

  it('shows a real empty state for a missing latest batch', async () => {
    fetchMock.mockResolvedValue(response({ detail: 'No processing batch found' }, 404))
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'No ingest batch yet' })).toBeInTheDocument()
    expect(screen.queryByText('Regulator fines Northwind Bank')).not.toBeInTheDocument()
  })

  it('shows a validation error for invalid pasted JSON', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('heading', { name: 'Latest batch complete' })

    await user.click(screen.getByRole('button', { name: /New run/i }))
    await user.click(screen.getByRole('button', { name: /Paste JSON/i }))
    fireEvent.change(screen.getByRole('textbox', { name: /Article JSON/i }), { target: { value: '{bad json' } })
    await user.click(screen.getByRole('button', { name: /Start ingest/i }))

    expect(screen.getByRole('alert')).toHaveTextContent('not valid JSON')
  })

  it('posts a new batch and loads it by the returned id', async () => {
    const user = userEvent.setup()
    const nextBatch = { ...completedBatch(), id: 'batch-2', fileName: 'demo-monitoring-batch.json' }
    fetchMock.mockImplementation(async (input, init) => {
      const url = String(input)
      if (url.endsWith('/processing-batches/latest')) return response({ detail: 'No processing batch found' }, 404)
      if (url.endsWith('/processing-batches') && init?.method === 'POST') {
        return response({ ...nextBatch, articles: undefined }, 202)
      }
      if (url.endsWith('/processing-batches/batch-2')) return response(nextBatch)
      return response({ detail: 'Unexpected request' }, 500)
    })
    render(<App />)
    await screen.findByRole('heading', { name: 'No ingest batch yet' })

    await user.click(screen.getByRole('button', { name: /New run/i }))
    await user.click(screen.getByRole('button', { name: /Load demo batch/i }))

    expect(await screen.findByText('Regulator fines Northwind Bank')).toBeInTheDocument()
    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')
    expect(String(postCall?.[0])).toMatch(/\/api\/v1\/processing-batches$/)
    expect(JSON.parse(String(postCall?.[1]?.body))).toMatchObject({
      fileName: 'demo-monitoring-batch.json',
      articles: expect.any(Array),
    })
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/api\/v1\/processing-batches\/batch-2$/), expect.any(Object))
  })

  it('keeps review decisions local and adds relevant articles to the local compilation', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('heading', { name: 'Latest batch complete' })

    const navigation = screen.getByRole('navigation', { name: 'Workflow stages' })
    const reviewTab = await waitFor(() => within(navigation).getByRole('button', { name: /Review.*1 pending/i }))
    await user.click(reviewTab)
    await user.click(screen.getByRole('button', { name: /^Relevant.*R$/i }))

    expect(within(navigation).getByRole('button', { name: /Compile.*2 in doc/i })).toBeInTheDocument()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
  })

  it('offers a retry after a backend error', async () => {
    fetchMock
      .mockResolvedValueOnce(response({ detail: 'Database unavailable' }, 503))
      .mockResolvedValueOnce(response(completedBatch()))
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Database unavailable')
    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByText('Regulator fines Northwind Bank')).toBeInTheDocument()
  })
})
