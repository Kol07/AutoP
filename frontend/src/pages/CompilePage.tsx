import { useMemo, useState } from 'react'
import {
  CalendarDays, Check, ChevronRight, Clock3, Copy, Download, FileText,
  History, LayoutList, Plus, Printer, Save, Sparkles,
} from 'lucide-react'
import type { Article, Compilation } from '../types'
import { formatDate, getLead } from '../utils/format'

interface CompilePageProps {
  articles: Article[]
  compilations: Compilation[]
  activeCompilationId: string
  onSelectCompilation: (id: string) => void
  onUpdateCompilation: (id: string, changes: Partial<Compilation>) => void
  onNewCompilation: () => void
  onDuplicateCompilation: (id: string) => void
  onSaveCompilation: (id: string) => void
  onPrototypeExport: (format: 'Markdown' | 'PDF') => void
}

export function CompilePage({ articles, compilations, activeCompilationId, onSelectCompilation, onUpdateCompilation, onNewCompilation, onDuplicateCompilation, onSaveCompilation, onPrototypeExport }: CompilePageProps) {
  const [railTab, setRailTab] = useState<'articles' | 'history'>('articles')
  const active = compilations.find((item) => item.id === activeCompilationId) ?? compilations[0]
  const relevantArticles = articles.filter((article) => article.reviewDecision === 'relevant')
  const selectedArticles = useMemo(
    () => active ? active.articleIds.map((id) => articles.find((article) => article.id === id)).filter((article): article is Article => Boolean(article)) : [],
    [active, articles],
  )
  const sourceCount = useMemo(() => new Set(selectedArticles.map((article) => article.source)).size, [selectedArticles])

  if (!active) return null

  function toggleArticle(articleId: string) {
    const articleIds = active.articleIds.includes(articleId)
      ? active.articleIds.filter((id) => id !== articleId)
      : [...active.articleIds, articleId]
    onUpdateCompilation(active.id, { articleIds })
  }

  return (
    <main className="compile-layout">
      <aside className="compile-sidebar">
        <div className="sidebar-heading"><div><div className="eyebrow">Briefing desk</div><h2>Build compilation</h2></div><button className="icon-button highlighted" onClick={onNewCompilation} aria-label="New compilation" title="New compilation"><Plus size={18} /></button></div>
        <div className="rail-tabs" role="tablist">
          <button className={railTab === 'articles' ? 'active' : ''} onClick={() => setRailTab('articles')}><LayoutList size={15} /> Articles <span>{relevantArticles.length}</span></button>
          <button className={railTab === 'history' ? 'active' : ''} onClick={() => setRailTab('history')}><History size={15} /> History <span>{compilations.length}</span></button>
        </div>

        {railTab === 'articles' ? (
          <div className="compile-article-list">
            <p className="rail-description">Relevant articles are automatically added. Fine-tune this briefing below.</p>
            {relevantArticles.map((article) => {
              const included = active.articleIds.includes(article.id)
              return (
                <button className={`compile-article ${included ? 'included' : ''}`} key={article.id} onClick={() => toggleArticle(article.id)}>
                  <span className="include-box">{included ? <Check size={13} /> : <Plus size={13} />}</span>
                  <span><strong>{article.title}</strong><small className="mono">{article.source} · SIM {article.confidence.toFixed(2)}</small></span>
                </button>
              )
            })}
            {!relevantArticles.length && <div className="empty-list"><Sparkles size={22} /><strong>No relevant articles yet</strong><span>Mark articles relevant during review.</span></div>}
          </div>
        ) : (
          <div className="history-list">
            <p className="rail-description">Reopen and edit saved briefings from this session.</p>
            {compilations.map((compilation) => (
              <button key={compilation.id} className={`history-item ${compilation.id === active.id ? 'active' : ''}`} onClick={() => onSelectCompilation(compilation.id)}>
                <span className="history-icon"><FileText size={17} /></span>
                <span><strong>{compilation.title || 'Untitled briefing'}</strong><small>{compilation.articleIds.length} articles · updated {formatDate(compilation.updatedAt)}</small></span>
                <ChevronRight size={15} />
              </button>
            ))}
          </div>
        )}
      </aside>

      <section className="compile-workspace">
        <div className="compile-toolbar">
          <div><div className="eyebrow">Stage 03 · Compile</div><p>{selectedArticles.length} of {relevantArticles.length} relevant articles in document</p></div>
          <div className="button-row">
            <div className="segmented-control" aria-label="Preview mode">
              <button className={active.previewMode === 'lead' ? 'active' : ''} onClick={() => onUpdateCompilation(active.id, { previewMode: 'lead' })}>Lead only</button>
              <button className={active.previewMode === 'full' ? 'active' : ''} onClick={() => onUpdateCompilation(active.id, { previewMode: 'full' })}>Full text</button>
            </div>
            <button className="button secondary" onClick={() => onDuplicateCompilation(active.id)}><Copy size={15} /> Duplicate</button>
            <button className="button secondary" onClick={() => onPrototypeExport('Markdown')}><Download size={15} /> .md</button>
            <button className="button secondary" onClick={() => onPrototypeExport('PDF')}><Printer size={15} /> PDF</button>
            <button className="button primary" onClick={() => onSaveCompilation(active.id)}><Save size={15} /> Save</button>
          </div>
        </div>

        <div className="compile-fields">
          <label><span className="eyebrow">Title</span><input value={active.title} onChange={(event) => onUpdateCompilation(active.id, { title: event.target.value })} /></label>
          <label><span className="eyebrow">Introduction</span><input value={active.introduction} onChange={(event) => onUpdateCompilation(active.id, { introduction: event.target.value })} /></label>
        </div>

        <div className="document-stage">
          <article className="document-preview">
            <header className="document-header"><span className="mono">AUTOPOROTW · COMPILED BRIEFING</span><span className="mono">{formatDate(active.updatedAt).toUpperCase()}</span></header>
            <h1>{active.title || 'Untitled briefing'}</h1>
            <p className="document-intro">{active.introduction || 'Add an introduction above to frame this compilation.'}</p>
            <div className="document-stats"><span>{selectedArticles.length} articles</span><span>{sourceCount} sources</span><span>Updated {formatDate(active.updatedAt, true)}</span></div>
            <div className="document-rule" />
            {selectedArticles.length ? (
              <div className="document-articles">
                {selectedArticles.map((article, index) => (
                  <section key={article.id} className="document-article">
                    <div className="document-article-meta"><span>{String(index + 1).padStart(2, '0')}</span><span>{article.source}</span><span>{formatDate(article.publishedAt)}</span></div>
                    <h2>{article.title}</h2>
                    <p>{active.previewMode === 'lead' ? getLead(article.content) : article.content}</p>
                  </section>
                ))}
              </div>
            ) : (
              <div className="document-empty"><FileText size={28} /><strong>Select articles to build this briefing</strong><span>Relevant articles are available in the left rail.</span></div>
            )}
            <footer className="document-footer"><span>AutoPOROTW intelligence brief</span><span>{selectedArticles.length ? 'Ready for review' : 'Draft'}</span></footer>
          </article>
        </div>

        <div className="workspace-status"><span><CalendarDays size={14} /> Created {formatDate(active.createdAt, true)}</span><span><Clock3 size={14} /> Last edited {formatDate(active.updatedAt, true)}</span></div>
      </section>
    </main>
  )
}
