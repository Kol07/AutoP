import { useCallback, useEffect, useState } from 'react'
import {
  createProcessingBatch,
  fetchLatestProcessingBatch,
  fetchProcessingBatch,
} from '../api/processingBatches'
import { ApiError } from '../api/apiClient'
import type { ArticleInput, ProcessingBatch } from '../types'

const POLL_INTERVAL_MS = 2_000

export function useProcessingBatch() {
  const [batch, setBatch] = useState<ProcessingBatch | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [pollAttempt, setPollAttempt] = useState(0)

  const loadLatest = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setBatch(await fetchLatestProcessingBatch())
    } catch (nextError) {
      if (nextError instanceof ApiError && nextError.status === 404) {
        setBatch(null)
      } else {
        setError(nextError instanceof Error ? nextError.message : 'Unable to load the latest batch.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const refresh = useCallback(async () => {
    setError('')
    try {
      const nextBatch = batch
        ? await fetchProcessingBatch(batch.id)
        : await fetchLatestProcessingBatch()
      setBatch(nextBatch)
    } catch (nextError) {
      if (nextError instanceof ApiError && nextError.status === 404) {
        setBatch(null)
      } else {
        setError(nextError instanceof Error ? nextError.message : 'Unable to refresh the batch.')
      }
    }
  }, [batch])

  const startBatch = useCallback(async (articles: ArticleInput[], fileName: string) => {
    setSubmitting(true)
    setError('')
    try {
      const summary = await createProcessingBatch(fileName, articles)
      setBatch({ ...summary, articles: [] })

      try {
        setBatch(await fetchProcessingBatch(summary.id))
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : 'The batch started, but its status could not be loaded yet.')
      }
    } catch (nextError) {
      const message = nextError instanceof Error ? nextError.message : 'Unable to start the ingest run.'
      setError(message)
      throw nextError
    } finally {
      setSubmitting(false)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    void fetchLatestProcessingBatch()
      .then((nextBatch) => {
        if (!cancelled) setBatch(nextBatch)
      })
      .catch((nextError: unknown) => {
        if (cancelled) return
        if (nextError instanceof ApiError && nextError.status === 404) {
          setBatch(null)
        } else {
          setError(nextError instanceof Error ? nextError.message : 'Unable to load the latest batch.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!batch || batch.status !== 'processing') return

    let cancelled = false

    const timer = window.setTimeout(async () => {
      try {
        const nextBatch = await fetchProcessingBatch(batch.id)
        if (!cancelled) {
          setBatch(nextBatch)
          setError('')
        }
      } catch (nextError) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : 'Unable to refresh the processing batch.')
        }
      } finally {
        if (!cancelled) setPollAttempt((attempt) => attempt + 1)
      }
    }, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [batch, pollAttempt])

  return {
    batch,
    error,
    loading,
    submitting,
    loadLatest,
    refresh,
    startBatch,
  }
}
