import { useEffect, useMemo, useState } from 'react'
import {
  ArrowDown, ArrowUp, BrainCircuit, Check, CheckCircle2,
  FilePlus2, Scale, Search, ShieldCheck, Sparkles, X,
} from 'lucide-react'
import type { Article, ReviewDecision } from '../types'
import { confidenceLabel, formatDate } from '../utils/format'

type ReviewFilter = ReviewDecision | 'all'
type ReviewSort = 'pipeline' | 'confidence' | 'hits'

interface ReviewPageProps {
  articles: Article[]
  onDecision: (articleId: string, decision: Exclude<ReviewDecision, 'pending'>) => void
  onNoteChange: (articleId: string, note: string) => void
  onCompile: () => void
}

export function ReviewPage({ articles, onDecision, onNoteChange, onCompile }: ReviewPageProps) {
  const reviewableArticles = useMemo(
    () => articles.filter((article) => article.classificationReady),
    [articles],
  )
  const [filter, setFilter] = useState<ReviewFilter>('pending')
  const [sort, setSort] = useState<ReviewSort>('pipeline')
  const [selectedId, setSelectedId] = useState<string>()

  const counts = useMemo(() => ({
    pending: reviewableArticles.filter((article) => article.reviewDecision === 'pending').length,
    relevant: reviewableArticles.filter((article) => article.reviewDecision === 'relevant').length,
    irrelevant: reviewableArticles.filter((article) => article.reviewDecision === 'irrelevant').length,
    all: reviewableArticles.length,
  }), [reviewableArticles])

  const visibleArticles = useMemo(() => {
    const filtered = filter === 'all'
      ? [...reviewableArticles]
      : reviewableArticles.filter((article) => article.reviewDecision === filter)
    if (sort === 'confidence') return filtered.sort((a, b) => (b.confidence ?? -1) - (a.confidence ?? -1))
    if (sort === 'hits') return filtered.sort((a, b) => b.guidelineHits.length - a.guidelineHits.length)
    return filtered.sort((a, b) => a.sequence - b.sequence)
  }, [reviewableArticles, filter, sort])

  const selected = reviewableArticles.find((article) => article.id === selectedId) ?? visibleArticles[0] ?? reviewableArticles[0]
  const selectedPosition = visibleArticles.findIndex((article) => article.id === selected?.id)

  function moveSelection(direction: -1 | 1) {
    if (!visibleArticles.length) return
    const current = Math.max(0, selectedPosition)
    const next = Math.min(visibleArticles.length - 1, Math.max(0, current + direction))
    setSelectedId(visibleArticles[next].id)
  }

  function decide(decision: Exclude<ReviewDecision, 'pending'>) {
    if (!selected) return
    onDecision(selected.id, decision)
    const currentIndex = visibleArticles.findIndex((article) => article.id === selected.id)
    const nextArticle = visibleArticles[currentIndex + 1] ?? visibleArticles[currentIndex - 1]
    if (filter === 'pending' && nextArticle) setSelectedId(nextArticle.id)
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement
      if (target.matches('textarea, input, select')) return
      if (event.key.toLowerCase() === 'j' || event.key === 'ArrowDown') { event.preventDefault(); moveSelection(1) }
      if (event.key.toLowerCase() === 'k' || event.key === 'ArrowUp') { event.preventDefault(); moveSelection(-1) }
      if (event.key.toLowerCase() === 'r') { event.preventDefault(); decide('relevant') }
      if (event.key.toLowerCase() === 'x') { event.preventDefault(); decide('irrelevant') }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  })

  return (
    <main className="review-layout">
      <aside className="review-sidebar">
        <div className="sidebar-heading"><div><div className="eyebrow">Decision desk</div><h2>Review queue</h2></div><span className="count-badge">{counts.pending}</span></div>
        <div className="review-filter" role="tablist" aria-label="Review status">
          {(['pending', 'relevant', 'irrelevant', 'all'] as ReviewFilter[]).map((value) => (
            <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>
              <span>{value === 'irrelevant' ? 'Not relevant' : value[0].toUpperCase() + value.slice(1)}</span>
              <strong>{counts[value]}</strong>
            </button>
          ))}
        </div>
        <label className="sort-control"><span>Sort by</span><select value={sort} onChange={(event) => setSort(event.target.value as ReviewSort)}><option value="pipeline">Pipeline order</option><option value="confidence">Highest confidence</option><option value="hits">Most guideline hits</option></select></label>
        <div className="review-list">
          {visibleArticles.length ? visibleArticles.map((article) => (
            <button key={article.id} className={`review-list-item ${selected?.id === article.id ? 'active' : ''}`} onClick={() => setSelectedId(article.id)}>
              <span className="mono item-meta">#{String(article.sequence).padStart(3, '0')} · {article.source}</span>
              <strong>{article.title}</strong>
              <span className="item-pills"><span className="score-pill">SIM {article.confidence === undefined ? 'N/A' : article.confidence.toFixed(2)}</span><span className={`hit-pill ${article.guidelineHits.length ? 'has-hits' : ''}`}>{article.guidelineHits.length} {article.guidelineHits.length === 1 ? 'HIT' : 'HITS'}</span></span>
            </button>
          )) : (
            <div className="empty-list"><Search size={22} /><strong>No articles here</strong><span>{reviewableArticles.length ? 'Try a different review filter.' : 'Articles appear after classification completes.'}</span></div>
          )}
        </div>
      </aside>

      <section className="review-detail">
        {selected ? (
          <>
            <div className="article-title-block">
              <div className="review-meta-row">
                <span className="eyebrow">Article #{String(selected.sequence).padStart(3, '0')} · {selected.source} · {formatDate(selected.publishedAt)}</span>
                <div className="article-stepper"><span>{Math.max(1, selectedPosition + 1)} / {visibleArticles.length || reviewableArticles.length}</span><button onClick={() => moveSelection(-1)} aria-label="Previous article"><ArrowUp size={16} /></button><button onClick={() => moveSelection(1)} aria-label="Next article"><ArrowDown size={16} /></button></div>
              </div>
              <h1>{selected.title}</h1>
            </div>

            <div className="signal-grid">
              <article className="signal-card panel blue">
                <div className="signal-heading"><span className="signal-icon"><BrainCircuit size={18} /></span><div><strong>Similarity coverage</strong><span className="mono">{selected.embeddingModel ?? 'embedding model'}</span></div><div className="signal-score"><strong>{selected.confidence === undefined ? 'N/A' : selected.confidence.toFixed(3)}</strong><span>{selected.confidence === undefined ? 'unavailable' : confidenceLabel(selected.confidence)}</span></div></div>
                <div className="match-list">
                  {selected.similarityMatches.map((match, index) => (
                    <div className="match-row" key={match.id}><span className="mono">{index + 1}</span><div><strong>{match.title}</strong><span className="match-bar"><i style={{ width: `${Math.max(0, match.score) * 100}%` }} /></span><small className="mono">{match.source} · {match.relevanceResult}</small></div><span className="mono">{match.score.toFixed(3)}</span></div>
                  ))}
                  {!selected.similarityMatches.length && <div className="no-signal"><Search size={20} /><span>No persisted similarity matches.</span></div>}
                </div>
              </article>

              <article className="signal-card panel amber">
                <div className="signal-heading"><span className="signal-icon"><Scale size={18} /></span><div><strong>Guideline check</strong><span className="mono">{selected.llmModel ?? 'classification model'}</span></div><div className="signal-score"><strong>{selected.guidelineHits.length}</strong><span>guideline {selected.guidelineHits.length === 1 ? 'hit' : 'hits'}</span></div></div>
                {selected.guidelineHits.length ? selected.guidelineHits.map((hit) => (
                  <div className="guideline-hit" key={hit.id}><div><span className="hit-code mono">{hit.id}</span></div><p>{hit.reason}</p></div>
                )) : <div className="no-signal"><ShieldCheck size={20} /><span>No guideline signal detected.</span></div>}
              </article>

              <article className="signal-card panel violet motherhood-card">
                <div className="signal-heading"><span className="signal-icon"><Sparkles size={18} /></span><div><strong>Public-interest check</strong><span className="mono">motherhood statement</span></div><span className={`decision-chip ${selected.motherhoodResult}`}>{selected.motherhoodResult ?? 'unavailable'}</span></div>
                <p>{selected.motherhoodReason || 'No persisted public-interest reason.'}</p>
              </article>
            </div>

            <article className="full-text-card panel"><div className="eyebrow">Full text · {selected.wordCount} words</div>{selected.content.split(/\n\s*\n/).map((paragraph, index) => <p key={`${index}-${paragraph.slice(0, 40)}`}>{paragraph}</p>)}</article>

            <label className="reviewer-note"><span className="eyebrow">Reviewer note · saved for this session only</span><textarea placeholder="Optional context — review persistence will be added later." value={selected.reviewerNote} onChange={(event) => onNoteChange(selected.id, event.target.value)} /></label>

            <div className="review-action-bar">
              <div className="shortcut-hint"><kbd>J</kbd><kbd>K</kbd><span>navigate</span><kbd>R</kbd><span>relevant</span><kbd>X</kbd><span>not relevant</span></div>
              <div className="button-row">
                <button className="button secondary" onClick={onCompile}><FilePlus2 size={16} /> View compilation</button>
                <button className={`button danger ${selected.reviewDecision === 'irrelevant' ? 'selected' : ''}`} onClick={() => decide('irrelevant')}><X size={16} /> Not relevant <kbd>X</kbd></button>
                <button className={`button primary ${selected.reviewDecision === 'relevant' ? 'selected' : ''}`} onClick={() => decide('relevant')}><Check size={16} /> Relevant <kbd>R</kbd></button>
              </div>
            </div>
          </>
        ) : (
          <div className="empty-detail"><CheckCircle2 size={34} /><h2>{reviewableArticles.length ? 'Queue clear' : 'Nothing ready for review'}</h2><p>{reviewableArticles.length ? 'No articles match this filter.' : 'Wait for the ingest pipeline to finish classifying articles.'}</p></div>
        )}
      </section>
    </main>
  )
}
