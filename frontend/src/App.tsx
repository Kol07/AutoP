import { useEffect, useMemo, useState } from 'react'
import { AppHeader } from './components/AppHeader'
import { Toast } from './components/Toast'
import { useProcessingBatch } from './hooks/useProcessingBatch'
import { CompilePage } from './pages/CompilePage'
import { IngestPage } from './pages/IngestPage'
import { ReviewPage } from './pages/ReviewPage'
import type { Article, Compilation, ReviewDecision, RunStatus, Stage } from './types'
import { mapBatchArticles } from './utils/processingBatch'
import './App.css'

function createCompilation(articles: Article[]): Compilation {
  const timestamp = new Date().toISOString()
  return {
    id: `comp-${Date.now()}`,
    title: 'Untitled briefing',
    introduction: 'Articles reviewed and marked relevant by the classification team.',
    articleIds: articles
      .filter((article) => article.reviewDecision === 'relevant')
      .map((article) => article.id),
    previewMode: 'lead',
    createdAt: timestamp,
    updatedAt: timestamp,
  }
}

interface WorkspaceProps {
  pipeline: ReturnType<typeof useProcessingBatch>
  stage: Stage
  setStage: (stage: Stage) => void
  setToast: (message: string) => void
}

function Workspace({ pipeline, stage, setStage, setToast }: WorkspaceProps) {
  const baseArticles = useMemo(
    () => pipeline.batch ? mapBatchArticles(pipeline.batch) : [],
    [pipeline.batch],
  )
  const [articleOverrides, setArticleOverrides] = useState<Record<string, Partial<Article>>>({})
  const articles = useMemo(
    () => baseArticles.map((article) => ({ ...article, ...articleOverrides[article.id] })),
    [articleOverrides, baseArticles],
  )
  const [initialCompilation] = useState(() => (
    pipeline.batch && pipeline.batch.status !== 'processing'
      ? createCompilation(baseArticles)
      : null
  ))
  const [compilations, setCompilations] = useState<Compilation[]>(() => initialCompilation ? [initialCompilation] : [])
  const [activeCompilationId, setActiveCompilationId] = useState(initialCompilation?.id ?? '')

  const pendingCount = articles.filter((article) => article.classificationReady && article.reviewDecision === 'pending').length
  const processedCount = pipeline.batch?.processedArticles ?? 0
  const activeCompilation = compilations.find((item) => item.id === activeCompilationId)
  const runStatus: RunStatus = pipeline.loading || pipeline.submitting || pipeline.batch?.status === 'processing'
    ? 'running'
    : pipeline.batch?.status === 'failed'
      ? 'failed'
      : pipeline.batch
        ? 'complete'
        : 'idle'

  function updateArticle(articleId: string, changes: Partial<Article>) {
    setArticleOverrides((current) => ({
      ...current,
      [articleId]: { ...current[articleId], ...changes },
    }))
  }

  function updateDecision(articleId: string, decision: Exclude<ReviewDecision, 'pending'>) {
    updateArticle(articleId, { reviewDecision: decision })
    setCompilations((current) => current.map((compilation) => {
      if (compilation.id !== activeCompilationId) return compilation
      const articleIds = decision === 'relevant'
        ? Array.from(new Set([...compilation.articleIds, articleId]))
        : compilation.articleIds.filter((id) => id !== articleId)
      return { ...compilation, articleIds, updatedAt: new Date().toISOString() }
    }))
  }

  function updateCompilation(id: string, changes: Partial<Compilation>) {
    setCompilations((current) => current.map((item) => item.id === id ? { ...item, ...changes } : item))
  }

  function newCompilation() {
    const compilation = createCompilation(articles)
    setCompilations((current) => [compilation, ...current])
    setActiveCompilationId(compilation.id)
    setToast('New briefing created')
  }

  function duplicateCompilation(id: string) {
    const source = compilations.find((item) => item.id === id)
    if (!source) return
    const timestamp = new Date().toISOString()
    const copy = { ...source, id: `comp-${Date.now()}`, title: `${source.title} — Copy`, createdAt: timestamp, updatedAt: timestamp }
    setCompilations((current) => [copy, ...current])
    setActiveCompilationId(copy.id)
    setToast('Compilation duplicated')
  }

  return (
    <>
      <AppHeader
        stage={stage}
        onStageChange={setStage}
        ingestCount={`${processedCount}/${pipeline.batch?.totalArticles ?? 0}`}
        reviewCount={`${pendingCount} pending`}
        compileCount={`${activeCompilation?.articleIds.length ?? 0} in doc`}
        runStatus={runStatus}
      />

      {stage === 'ingest' && (
        <IngestPage
          articles={articles}
          batch={pipeline.batch}
          runStatus={runStatus}
          loading={pipeline.loading}
          submitting={pipeline.submitting}
          error={pipeline.error}
          onStart={pipeline.startBatch}
          onRefresh={pipeline.refresh}
          onRetry={pipeline.loadLatest}
          onReview={() => setStage('review')}
        />
      )}
      {stage === 'review' && (
        <ReviewPage
          articles={articles}
          onDecision={updateDecision}
          onNoteChange={(articleId, reviewerNote) => updateArticle(articleId, { reviewerNote })}
          onCompile={() => setStage('compile')}
        />
      )}
      {stage === 'compile' && (
        <CompilePage
          articles={articles}
          compilations={compilations}
          activeCompilationId={activeCompilationId}
          onSelectCompilation={setActiveCompilationId}
          onUpdateCompilation={updateCompilation}
          onNewCompilation={newCompilation}
          onDuplicateCompilation={duplicateCompilation}
          onSaveCompilation={(id) => {
            updateCompilation(id, { updatedAt: new Date().toISOString() })
            setToast('Briefing saved for this session')
          }}
          onPrototypeExport={(format) => setToast(`${format} export is visual-only in this prototype`)}
        />
      )}
    </>
  )
}

function App() {
  const [stage, setStage] = useState<Stage>('ingest')
  const [toast, setToast] = useState('')
  const pipeline = useProcessingBatch()
  const workspaceKey = `${pipeline.batch?.id ?? 'empty'}-${pipeline.batch?.status === 'processing' ? 'processing' : 'settled'}`

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 3200)
    return () => window.clearTimeout(timer)
  }, [toast])

  return (
    <div className="app-shell">
      <Workspace
        key={workspaceKey}
        pipeline={pipeline}
        stage={stage}
        setStage={setStage}
        setToast={setToast}
      />
      {toast && <Toast message={toast} onClose={() => setToast('')} />}
    </div>
  )
}

export default App
