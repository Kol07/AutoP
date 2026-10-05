import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react'
import { createArticleFromInput } from '../data/demoData'
import type { Article, ArticleInput, RunStatus } from '../types'

interface PipelineOptions {
  articles: Article[]
  setArticles: Dispatch<SetStateAction<Article[]>>
}

export function usePipelineSimulation({ articles, setArticles }: PipelineOptions) {
  const [runStatus, setRunStatus] = useState<RunStatus>('complete')
  const [fileName, setFileName] = useState('monitoring-batch-2026-10-05.json')
  const [elapsedMs, setElapsedMs] = useState(7420)
  const startedAt = useRef<number | null>(null)
  const elapsedBeforePause = useRef(0)

  const startBatch = useCallback((inputs: ArticleInput[], nextFileName: string) => {
    setArticles(inputs.map((input, index) => createArticleFromInput(input, index, true)))
    setFileName(nextFileName)
    setElapsedMs(0)
    elapsedBeforePause.current = 0
    startedAt.current = performance.now()
    setRunStatus('running')
  }, [setArticles])

  const pause = useCallback(() => {
    if (runStatus !== 'running' || startedAt.current === null) return
    elapsedBeforePause.current += performance.now() - startedAt.current
    startedAt.current = null
    setElapsedMs(elapsedBeforePause.current)
    setRunStatus('paused')
  }, [runStatus])

  const resume = useCallback(() => {
    if (runStatus !== 'paused') return
    startedAt.current = performance.now()
    setRunStatus('running')
  }, [runStatus])

  const restart = useCallback(() => {
    const inputs = articles.map((article) => ({
      recordTitle: article.title,
      recordContent: article.content,
      recordSourceName: article.source,
      recordISOTimeStamp: article.publishedAt,
    }))
    startBatch(inputs, fileName)
  }, [articles, fileName, startBatch])

  useEffect(() => {
    if (runStatus !== 'running') return
    const elapsedTimer = window.setInterval(() => {
      if (startedAt.current !== null) setElapsedMs(elapsedBeforePause.current + performance.now() - startedAt.current)
    }, 100)
    return () => window.clearInterval(elapsedTimer)
  }, [runStatus])

  useEffect(() => {
    if (runStatus !== 'running') return
    const workflowTimer = window.setInterval(() => {
      setArticles((current) => {
        const activeIndex = current.findIndex((article) =>
          Object.values(article.workflows).some((task) => task.status !== 'complete'),
        )
        if (activeIndex === -1) return current

        return current.map((article, index) => {
          if (index !== activeIndex) return article
          const { embedding, similarity, llm } = article.workflows
          if (embedding.status === 'queued') {
            return { ...article, workflows: { ...article.workflows, embedding: { status: 'running' } } }
          }
          if (embedding.status === 'running') {
            return { ...article, workflows: { ...article.workflows, embedding: { status: 'complete', durationMs: 310 + index * 29 } } }
          }
          if (similarity.status === 'queued' || llm.status === 'queued') {
            return {
              ...article,
              workflows: {
                ...article.workflows,
                similarity: { status: 'running' },
                llm: { status: 'running' },
              },
            }
          }
          return {
            ...article,
            workflows: {
              ...article.workflows,
              similarity: { status: 'complete', durationMs: 440 + index * 37 },
              llm: { status: 'complete', durationMs: 880 + index * 83 },
            },
          }
        })
      })
    }, 430)
    return () => window.clearInterval(workflowTimer)
  }, [runStatus, setArticles])

  useEffect(() => {
    if (
      runStatus !== 'running' ||
      articles.length === 0 ||
      !articles.every((article) =>
        Object.values(article.workflows).every((task) => task.status === 'complete'),
      )
    ) return

    if (startedAt.current !== null) {
      elapsedBeforePause.current += performance.now() - startedAt.current
    }
    startedAt.current = null
    setElapsedMs(elapsedBeforePause.current)
    setRunStatus('complete')
  }, [articles, runStatus])

  return { runStatus, fileName, elapsedMs, startBatch, pause, resume, restart }
}
