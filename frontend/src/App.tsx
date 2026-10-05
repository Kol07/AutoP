import { useEffect, useState } from 'react'
import { AppHeader } from './components/AppHeader'
import { Toast } from './components/Toast'
import { demoArticles, demoCompilations } from './data/demoData'
import { usePipelineSimulation } from './hooks/usePipelineSimulation'
import { CompilePage } from './pages/CompilePage'
import { IngestPage } from './pages/IngestPage'
import { ReviewPage } from './pages/ReviewPage'
import type { Article, Compilation, ReviewDecision, Stage } from './types'
import './App.css'

function App() {
  const [stage, setStage] = useState<Stage>('ingest')
  const [articles, setArticles] = useState<Article[]>(demoArticles)
  const [compilations, setCompilations] = useState<Compilation[]>(demoCompilations)
  const [activeCompilationId, setActiveCompilationId] = useState(demoCompilations[0].id)
  const [toast, setToast] = useState('')
  const pipeline = usePipelineSimulation({ articles, setArticles })

  const pendingCount = articles.filter((article) => article.reviewDecision === 'pending').length
  const processedCount = articles.filter((article) => Object.values(article.workflows).every((task) => task.status === 'complete')).length
  const activeCompilation = compilations.find((item) => item.id === activeCompilationId)

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 3200)
    return () => window.clearTimeout(timer)
  }, [toast])

  function updateDecision(articleId: string, decision: Exclude<ReviewDecision, 'pending'>) {
    setArticles((current) => current.map((article) => article.id === articleId ? { ...article, reviewDecision: decision } : article))
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
    const timestamp = new Date().toISOString()
    const compilation: Compilation = {
      id: `comp-${Date.now()}`,
      title: 'Untitled briefing',
      introduction: 'Articles reviewed and marked relevant by the classification team.',
      articleIds: articles.filter((article) => article.reviewDecision === 'relevant').map((article) => article.id),
      previewMode: 'lead',
      createdAt: timestamp,
      updatedAt: timestamp,
    }
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
    <div className="app-shell">
      <AppHeader
        stage={stage}
        onStageChange={setStage}
        ingestCount={`${processedCount}/${articles.length}`}
        reviewCount={`${pendingCount} pending`}
        compileCount={`${activeCompilation?.articleIds.length ?? 0} in doc`}
        runStatus={pipeline.runStatus}
      />

      {stage === 'ingest' && (
        <IngestPage
          articles={articles}
          runStatus={pipeline.runStatus}
          fileName={pipeline.fileName}
          elapsedMs={pipeline.elapsedMs}
          onStart={pipeline.startBatch}
          onPause={pipeline.pause}
          onResume={pipeline.resume}
          onRestart={pipeline.restart}
          onReview={() => setStage('review')}
        />
      )}
      {stage === 'review' && (
        <ReviewPage
          articles={articles}
          onDecision={updateDecision}
          onNoteChange={(articleId, reviewerNote) => setArticles((current) => current.map((article) => article.id === articleId ? { ...article, reviewerNote } : article))}
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
      {toast && <Toast message={toast} onClose={() => setToast('')} />}
    </div>
  )
}

export default App
