import { useState } from 'react'
import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Article } from '../types'
import { usePipelineSimulation } from './usePipelineSimulation'

describe('usePipelineSimulation', () => {
  afterEach(() => vi.useRealTimers())

  it('freezes elapsed time when every workflow has completed', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => {
      const [articles, setArticles] = useState<Article[]>([])
      return {
        articles,
        pipeline: usePipelineSimulation({ articles, setArticles }),
      }
    })

    act(() => {
      result.current.pipeline.startBatch([{
        recordTitle: 'Test article',
        recordContent: 'A short article used to verify pipeline completion.',
      }], 'test.json')
    })

    act(() => vi.advanceTimersByTime(2_000))

    expect(result.current.pipeline.runStatus).toBe('complete')
    const completedElapsed = result.current.pipeline.elapsedMs

    act(() => vi.advanceTimersByTime(5_000))

    expect(result.current.pipeline.elapsedMs).toBe(completedElapsed)
  })
})
