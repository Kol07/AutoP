import { describe, expect, it } from 'vitest'
import { parseArticleJson } from './ingest'

describe('parseArticleJson', () => {
  it('accepts the backend-compatible article shape', () => {
    const result = parseArticleJson(JSON.stringify([{
      recordTitle: 'A material development',
      recordContent: 'Article body',
      recordSourceName: 'Wire Service',
      recordISOTimeStamp: '2026-10-05T08:00:00Z',
    }]))

    expect(result.ok).toBe(true)
    if (result.ok) expect(result.data[0].recordSourceName).toBe('Wire Service')
  })

  it('returns actionable errors for malformed JSON', () => {
    expect(parseArticleJson('[invalid')).toEqual({
      ok: false,
      error: 'This is not valid JSON. Check brackets, commas, and quotation marks.',
    })
  })

  it('identifies rows missing required fields', () => {
    const result = parseArticleJson(JSON.stringify([{ recordTitle: 'Missing content' }]))
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error).toContain('article 1')
  })
})
