import { useMemo, useState, type ChangeEvent, type DragEvent } from 'react'
import {
  ArrowRight, BrainCircuit, Check, Clock3, FileJson2, History,
  LoaderCircle, RefreshCcw, ScanSearch, Sparkles, UploadCloud, X,
} from 'lucide-react'
import { demoInputs } from '../data/demoData'
import type { Article, ArticleInput, ProcessingBatch, RunStatus, TaskStatus } from '../types'
import { formatDate } from '../utils/format'
import { parseArticleJson } from '../utils/ingest'

interface IngestPageProps {
  articles: Article[]
  batch: ProcessingBatch | null
  runStatus: RunStatus
  loading: boolean
  submitting: boolean
  error: string
  onStart: (articles: ArticleInput[], fileName: string) => Promise<void>
  onRefresh: () => Promise<void>
  onRetry: () => Promise<void>
  onReview: () => void
}

const taskMeta = {
  embedding: { label: 'Embedding vector', icon: BrainCircuit, tone: 'blue' },
  similarity: { label: 'Similarity search', icon: ScanSearch, tone: 'violet' },
  llm: { label: 'Guideline classification', icon: Sparkles, tone: 'amber' },
} as const

function TaskStatusIcon({ status }: { status: TaskStatus }) {
  if (status === 'complete') return <Check size={14} />
  if (status === 'running') return <LoaderCircle size={14} className="spin" />
  if (status === 'failed') return <X size={14} />
  return <Clock3 size={14} />
}

export function IngestPage({
  articles,
  batch,
  runStatus,
  loading,
  submitting,
  error: requestError,
  onStart,
  onRefresh,
  onRetry,
  onReview,
}: IngestPageProps) {
  const [launcherOpen, setLauncherOpen] = useState(false)
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload')
  const [rawJson, setRawJson] = useState(JSON.stringify(demoInputs, null, 2))
  const [selectedFile, setSelectedFile] = useState<{ name: string; contents: string } | null>(null)
  const [validationError, setValidationError] = useState('')
  const [dragging, setDragging] = useState(false)

  const completeCount = batch?.processedArticles ?? 0
  const totalCount = batch?.totalArticles ?? 0
  const progress = totalCount ? Math.round((completeCount / totalCount) * 100) : 0
  const activeArticle = articles.find((article) => !article.classificationReady)
    ?? articles.at(-1)
  const activeIndex = activeArticle ? articles.findIndex((article) => article.id === activeArticle.id) : -1
  const flaggedCount = articles.filter((article) => article.classificationReady && article.guidelineHits.length > 0).length
  const pendingCount = articles.filter((article) => article.classificationReady && article.reviewDecision === 'pending').length
  const sourceCount = useMemo(() => new Set(articles.map((article) => article.source)).size, [articles])

  async function start(contents: string, nextFileName: string) {
    const parsed = parseArticleJson(contents)
    if (!parsed.ok) {
      setValidationError(parsed.error)
      return
    }

    setValidationError('')
    try {
      await onStart(parsed.data, nextFileName)
      setLauncherOpen(false)
    } catch (nextError) {
      setValidationError(nextError instanceof Error ? nextError.message : 'Unable to start the ingest run.')
    }
  }

  async function readFile(file?: File) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.json')) {
      setValidationError('Choose a .json file containing an array of articles.')
      return
    }
    const contents = await file.text()
    setSelectedFile({ name: file.name, contents })
    setValidationError('')
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    void readFile(event.dataTransfer.files[0])
  }

  function handleFileInput(event: ChangeEvent<HTMLInputElement>) {
    void readFile(event.target.files?.[0])
  }

  const heading = loading && !batch
    ? 'Loading the latest batch'
    : !batch
      ? 'No ingest batch yet'
      : runStatus === 'running'
        ? `Processing ${completeCount} of ${totalCount} articles`
        : runStatus === 'failed'
          ? 'Latest batch failed'
          : 'Latest batch complete'

  return (
    <main className="page ingest-page">
      <section className="run-overview panel">
        <div className="eyebrow">Stage 01 · Ingest</div>
        <div className="run-heading-row">
          <div>
            <h1>{heading}</h1>
            <p className="mono muted">
              {batch
                ? `${batch.fileName} · ${totalCount} articles · ${sourceCount} sources · started ${formatDate(batch.createdAt, true)}`
                : 'Upload or paste an article JSON file to create a processing batch.'}
            </p>
          </div>
          <div className="button-row">
            <button className="button secondary" onClick={() => void onRefresh()} disabled={loading || submitting}>
              <RefreshCcw size={16} /> Refresh
            </button>
            <button className="button secondary" onClick={() => setLauncherOpen((value) => !value)} disabled={submitting}>
              <FileJson2 size={16} /> New run
            </button>
            <button className="button primary" onClick={onReview} disabled={completeCount === 0}>
              Review <span>({pendingCount})</span><ArrowRight size={16} />
            </button>
          </div>
        </div>

        {requestError && (
          <div className="error-banner" role="alert">
            <X size={16} />
            <span>{requestError}</span>
            <button className="button ghost small" onClick={() => void onRetry()}>Retry</button>
          </div>
        )}

        <div className="segmented-progress" aria-label={`${progress}% complete`}>
          {articles.map((article) => (
            <span key={article.id} className={article.classificationReady ? 'complete' : batch?.status === 'failed' ? 'failed' : 'queued'} />
          ))}
        </div>
        <div className="progress-caption mono"><span>{completeCount}/{totalCount} processed</span><span>{progress}%</span></div>

        <div className="metric-strip">
          <div><span>Processed</span><strong>{completeCount}</strong></div>
          <div><span>Signals flagged</span><strong className="blue-text">{flaggedCount}</strong></div>
          <div><span>Awaiting review</span><strong className="amber-text">{pendingCount}</strong></div>
          <div><span>Batch status</span><strong>{batch?.status.replace('_', ' ') ?? 'none'}</strong></div>
        </div>
      </section>

      {launcherOpen && (
        <section className="ingest-launcher panel" aria-label="Start a new ingest run">
          <div className="section-heading">
            <div><div className="eyebrow">New batch</div><h2>Bring in article data</h2></div>
            <button className="icon-button" onClick={() => setLauncherOpen(false)} aria-label="Close new run panel"><X size={18} /></button>
          </div>
          <div className="tabs" role="tablist">
            <button className={inputMode === 'upload' ? 'active' : ''} onClick={() => setInputMode('upload')}>Upload JSON</button>
            <button className={inputMode === 'paste' ? 'active' : ''} onClick={() => setInputMode('paste')}>Paste JSON</button>
          </div>
          {inputMode === 'upload' ? (
            <div
              className={`drop-zone ${dragging ? 'dragging' : ''}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
            >
              <UploadCloud size={28} />
              <strong>{selectedFile?.name ?? 'Drop an article JSON file here'}</strong>
              <span>{selectedFile ? 'Ready to validate and run' : 'or choose a file from your computer'}</span>
              <label className="button secondary file-button">Choose file<input type="file" accept="application/json,.json" onChange={handleFileInput} /></label>
            </div>
          ) : (
            <textarea className="json-editor mono" value={rawJson} onChange={(event) => setRawJson(event.target.value)} aria-label="Article JSON" spellCheck={false} />
          )}
          {validationError && <div className="error-banner" role="alert"><X size={16} />{validationError}</div>}
          <div className="launcher-actions">
            <button className="button ghost" onClick={() => void start(JSON.stringify(demoInputs), 'demo-monitoring-batch.json')} disabled={submitting}><History size={16} /> Load demo batch</button>
            <button
              className="button primary"
              onClick={() => void (inputMode === 'paste' ? start(rawJson, 'pasted-articles.json') : selectedFile && start(selectedFile.contents, selectedFile.name))}
              disabled={submitting || (inputMode === 'upload' && !selectedFile)}
            >
              {submitting ? <LoaderCircle size={16} className="spin" /> : <ArrowRight size={16} />}
              {submitting ? 'Starting…' : 'Start ingest'}
            </button>
          </div>
        </section>
      )}

      {activeArticle ? (
        <>
          <section className="active-workflow-grid">
            <article className="article-focus panel">
              <div className="card-kicker"><span>Article #{String(activeArticle.sequence).padStart(3, '0')}</span><span>{activeArticle.wordCount} words</span></div>
              <h2>{activeArticle.title}</h2>
              <p className="mono muted">{activeArticle.source} · {formatDate(activeArticle.publishedAt)}</p>
              <p className="article-excerpt">{activeArticle.content.split('\n')[0]}</p>
            </article>

            <div className="workflow-stack">
              {(Object.keys(taskMeta) as Array<keyof typeof taskMeta>).map((key) => {
                const task = activeArticle.workflows[key]
                const meta = taskMeta[key]
                const Icon = meta.icon
                const model = key === 'embedding'
                  ? activeArticle.embeddingModel ?? 'embedding model'
                  : key === 'llm'
                    ? activeArticle.llmModel ?? 'classification model'
                    : 'pgvector · cosine'
                return (
                  <article className={`workflow-card panel ${meta.tone} ${task.status}`} key={key}>
                    <div className="workflow-icon"><Icon size={18} /></div>
                    <div className="workflow-copy"><strong>{meta.label}</strong><span className="mono">{model}</span></div>
                    <div className="workflow-status mono"><TaskStatusIcon status={task.status} />{task.status}</div>
                    <div className="task-line"><span /></div>
                  </article>
                )
              })}
            </div>
          </section>

          <section className="queue-panel panel">
            <div className="queue-header"><strong>Article queue</strong><span className="mono muted">persisted workflow state</span></div>
            <div className="queue-list">
              {articles.map((article) => {
                const state = article.classificationReady ? 'complete' : batch?.status === 'failed' ? 'failed' : 'queued'
                return (
                  <div className={`queue-row ${state}`} key={article.id}>
                    <span className="queue-index mono">{String(article.sequence).padStart(2, '0')}</span>
                    <div><strong>{article.title}</strong><span className="mono">{article.source}</span></div>
                    <span className="score-pill">SIM {article.confidence === undefined ? 'N/A' : article.confidence.toFixed(2)}</span>
                    <span className={`hit-pill ${article.guidelineHits.length ? 'has-hits' : ''}`}>{article.guidelineHits.length} {article.guidelineHits.length === 1 ? 'HIT' : 'HITS'}</span>
                    <span className={`row-status ${state}`}><TaskStatusIcon status={state === 'complete' ? 'complete' : state === 'failed' ? 'failed' : 'queued'} />{state}</span>
                  </div>
                )
              })}
            </div>
            <div className="queue-footer"><span className="mono muted">Showing article {activeIndex + 1} of {articles.length}</span></div>
          </section>
        </>
      ) : (
        <section className="panel empty-detail ingest-empty">
          <FileJson2 size={30} />
          <h2>{loading ? 'Loading batch data' : 'No articles to display'}</h2>
          <p>{loading ? 'Fetching the latest persisted processing state.' : 'Start a new ingest run to populate the queue.'}</p>
        </section>
      )}
    </main>
  )
}
