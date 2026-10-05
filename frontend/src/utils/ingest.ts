import type { ArticleInput } from '../types'

export type ParseResult =
  | { ok: true; data: ArticleInput[] }
  | { ok: false; error: string }

export function parseArticleJson(raw: string): ParseResult {
  if (!raw.trim()) return { ok: false, error: 'Add a JSON array before starting the run.' }

  let value: unknown
  try {
    value = JSON.parse(raw)
  } catch {
    return { ok: false, error: 'This is not valid JSON. Check brackets, commas, and quotation marks.' }
  }

  if (!Array.isArray(value)) {
    return { ok: false, error: 'The top-level JSON value must be an array of articles.' }
  }
  if (value.length === 0) {
    return { ok: false, error: 'The article array is empty.' }
  }

  const invalidRows: number[] = []
  const data: ArticleInput[] = []
  value.forEach((item, index) => {
    if (
      typeof item !== 'object' || item === null ||
      typeof (item as Record<string, unknown>).recordTitle !== 'string' ||
      !(item as Record<string, unknown>).recordTitle ||
      typeof (item as Record<string, unknown>).recordContent !== 'string' ||
      !(item as Record<string, unknown>).recordContent
    ) {
      invalidRows.push(index + 1)
      return
    }

    const row = item as Record<string, unknown>
    if (row.recordSourceName !== undefined && typeof row.recordSourceName !== 'string') {
      invalidRows.push(index + 1)
      return
    }
    if (row.recordISOTimeStamp !== undefined && (typeof row.recordISOTimeStamp !== 'string' || Number.isNaN(Date.parse(row.recordISOTimeStamp)))) {
      invalidRows.push(index + 1)
      return
    }

    data.push({
      recordTitle: (row.recordTitle as string).trim(),
      recordContent: (row.recordContent as string).trim(),
      recordSourceName: row.recordSourceName as string | undefined,
      recordISOTimeStamp: row.recordISOTimeStamp as string | undefined,
    })
  })

  if (invalidRows.length) {
    return {
      ok: false,
      error: `Fix article ${invalidRows.slice(0, 5).join(', ')}${invalidRows.length > 5 ? ' and others' : ''}. Each row needs non-empty recordTitle and recordContent strings.`,
    }
  }
  return { ok: true, data }
}
