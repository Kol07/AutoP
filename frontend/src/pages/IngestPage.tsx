import { useMemo, useState, type ChangeEvent, type DragEvent } from 'react'
import {
  ArrowRight, BrainCircuit, Check, CirclePause, CirclePlay, Clock3,
  FileJson2, History, LoaderCircle, RefreshCcw, ScanSearch, Sparkles, UploadCloud, X,
} from 'lucide-react'
import { demoInputs } from '../data/demoData'
import type { Article, ArticleInput, RunStatus, TaskStatus } from '../types'
import { formatDate, formatDuration } from '../utils/format'
import { parseArticleJson } from '../utils/ingest'

interface IngestPageProps {
  articles: Article[]
  runStatus: RunStatus
  fileName: string
  elapsedMs: number
  onStart: (articles: ArticleInput[], fileName: string) => void
  onPause: () => void
  onResume: () => void
  onRestart: () => void
  onReview: () => void
}

const taskMeta = {
  embedding: { label: 'Embedding vector', model: 'qwen3-embedding-4b', icon: BrainCircuit, tone: 'blue' },
  similarity: { label: 'Similarity search', model: 'pgvector · cosine', icon: ScanSearch, tone: 'violet' },
  llm: { label: 'Guideline classification', model: 'qwen3.8-27B-FP8', icon: Sparkles, tone: 'amber' },
} as const

function TaskStatusIcon({ status }: { status: TaskStatus }) {
  if (status === 'complete') return <Check size={14} />
  if (status === 'running') return <LoaderCircle size={14} className="spin" />
  if (status === 'failed') return <X size={14} />
  return <Clock3 size={14} />
}

export function IngestPage({ articles, runStatus, fileName, elapsedMs, onStart, onPause, onResume, onRestart, onReview }: IngestPageProps) {
  const [launcherOpen, setLauncherOpen] = useState(false)
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload')
  const [rawJson, setRawJson] = useState(JSON.stringify(demoInputs.slice(0, 3), null, 2))
  const [selectedFile, setSelectedFile] = useState<{ name: string; contents: string } | null>(null)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)

  const completeCount = articles.filter((article) => Object.values(article.workflows).every((task) => task.status === 'complete')).length
  const taskCount = articles.length * 3
  const completeTasks = articles.reduce((count, article) => count + Object.values(article.workflows).filter((task) => task.status === 'complete').length, 0)
  const progress = taskCount ? Math.round((completeTasks / taskCount) * 100) : 0
  const activeArticle = articles.find((article) => Object.values(article.workflows).some((task) => task.status === 'running'))
    ?? articles.find((article) => Object.values(article.workflows).some((task) => task.status === 'queued'))
    ?? articles.at(-1)
  const activeIndex = activeArticle ? articles.findIndex((article) => article.id === activeArticle.id) : 0
  const flaggedCount = articles.filter((article) => article.guidelineHits.length > 0 && Object.values(article.workflows).every((task) => task.status === 'complete')).length
  const pendingCount = articles.filter((article) => article.reviewDecision === 'pending' && Object.values(article.workflows).every((task) => task.status === 'complete')).length

  const sourceCount = useMemo(() => new Set(articles.map((article) => article.source)).size, [articles])

  function start(contents: string, nextFileName: string) {
    const parsed = parseArticleJson(contents)
    if (!parsed.ok) {
      setError(parsed.error)
      return
    }
    setError('')
    setLauncherOpen(false)
    onStart(parsed.data, nextFileName)
  }

  async function readFile(file?: File) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.json')) {
      setError('Choose a .json file containing an array of articles.')
      return
    }
    const contents = await file.text()
    setSelectedFile({ name: file.name, contents })
    setError('')
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    void readFile(event.dataTransfer.files[0])
  }

  function handleFileInput(event: ChangeEvent<HTMLInputElement>) {
    void readFile(event.target.files?.[0])
  }

  return (
    <main className="page ingest-page">
      <section className="run-overview panel">
        <div className="eyebrow">Stage 01 · Ingest</div>
        <div className="run-heading-row">
          <div>
            <h1>{runStatus === 'running' ? `Processing article ${Math.min(activeIndex + 1, articles.length)} of ${articles.length}` : runStatus === 'paused' ? 'Processing paused' : 'Latest batch complete'}</h1>
            <p className="mono muted">{fileName} · {articles.length} articles · {sourceCount} sources · elapsed {formatDuration(elapsedMs)}</p>
          </div>
          <div className="button-row">
            {runStatus === 'running' && <button className="button secondary" onClick={onPause}><CirclePause size={16} /> Pause</button>}
            {runStatus === 'paused' && <button className="button secondary" onClick={onResume}><CirclePlay size={16} /> Resume</button>}
            <button className="button secondary" onClick={() => setLauncherOpen((value) => !value)}><FileJson2 size={16} /> New run</button>
            <button className="button primary" onClick={onReview}>Review <span>({pendingCount})</span><ArrowRight size={16} /></button>
          </div>
        </div>

        <div className="segmented-progress" aria-label={`${progress}% complete`}>
          {articles.map((article) => {
            const statuses = Object.values(article.workflows).map((task) => task.status)
            const state = statuses.every((status) => status === 'complete') ? 'complete' : statuses.some((status) => status === 'running') ? 'active' : 'queued'
            return <span key={article.id} className={state} />
          })}
        </div>
        <div className="progress-caption mono"><span>{completeCount}/{articles.length} processed</span><span>{progress}%</span></div>

        <div className="metric-strip">
          <div><span>Processed</span><strong>{completeCount}</strong></div>
          <div><span>Signals flagged</span><strong className="blue-text">{flaggedCount}</strong></div>
          <div><span>Awaiting review</span><strong className="amber-text">{pendingCount}</strong></div>
          <div><span>Elapsed time</span><strong>{formatDuration(elapsedMs)}</strong></div>
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
          {error && <div className="error-banner" role="alert"><X size={16} />{error}</div>}
          <div className="launcher-actions">
            <button className="button ghost" onClick={() => start(JSON.stringify(demoInputs), 'demo-monitoring-batch.json')}><History size={16} /> Load demo batch</button>
            <button className="button primary" onClick={() => inputMode === 'paste' ? start(rawJson, 'pasted-articles.json') : selectedFile && start(selectedFile.contents, selectedFile.name)} disabled={inputMode === 'upload' && !selectedFile}>Start ingest <ArrowRight size={16} /></button>
          </div>
        </section>
      )}

      <section className="active-workflow-grid">
        <article className="article-focus panel">
          <div className="card-kicker"><span>Article #{String(activeArticle?.sequence ?? 0).padStart(3, '0')}</span><span>{activeArticle?.wordCount ?? 0} words</span></div>
          <h2>{activeArticle?.title ?? 'No article selected'}</h2>
          <p className="mono muted">{activeArticle?.source} · {formatDate(activeArticle?.publishedAt)}</p>
          <p className="article-excerpt">{activeArticle?.content.split('\n')[0]}</p>
        </article>

        <div className="workflow-stack">
          {(Object.keys(taskMeta) as Array<keyof typeof taskMeta>).map((key) => {
            const task = activeArticle?.workflows[key] ?? { status: 'queued' as const }
            const meta = taskMeta[key]
            const Icon = meta.icon
            return (
              <article className={`workflow-card panel ${meta.tone} ${task.status}`} key={key}>
                <div className="workflow-icon"><Icon size={18} /></div>
                <div className="workflow-copy"><strong>{meta.label}</strong><span className="mono">{meta.model}</span></div>
                <div className="workflow-status mono"><TaskStatusIcon status={task.status} />{task.status}{task.durationMs ? ` · ${formatDuration(task.durationMs)}` : ''}</div>
                <div className="task-line"><span /></div>
              </article>
            )
          })}
        </div>
      </section>

      <section className="queue-panel panel">
        <div className="queue-header"><strong>Article queue</strong><span className="mono muted">sequential · 3 workflows per article</span></div>
        <div className="queue-list">
          {articles.map((article) => {
            const statuses = Object.values(article.workflows).map((task) => task.status)
            const state = statuses.every((status) => status === 'complete') ? 'complete' : statuses.some((status) => status === 'running') ? 'active' : 'queued'
            return (
              <div className={`queue-row ${state}`} key={article.id}>
                <span className="queue-index mono">{String(article.sequence).padStart(2, '0')}</span>
                <div><strong>{article.title}</strong><span className="mono">{article.source}</span></div>
                <span className="score-pill">SIM {article.confidence.toFixed(2)}</span>
                <span className={`hit-pill ${article.guidelineHits.length ? 'has-hits' : ''}`}>{article.guidelineHits.length} {article.guidelineHits.length === 1 ? 'HIT' : 'HITS'}</span>
                <span className={`row-status ${state}`}><TaskStatusIcon status={state === 'active' ? 'running' : state === 'complete' ? 'complete' : 'queued'} />{state}</span>
              </div>
            )
          })}
        </div>
        <div className="queue-footer"><button className="button ghost small" onClick={onRestart}><RefreshCcw size={14} /> Restart simulation</button></div>
      </section>
    </main>
  )
}
