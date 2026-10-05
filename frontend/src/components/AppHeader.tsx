import { Activity, CheckCircle2, Layers3 } from 'lucide-react'
import type { RunStatus, Stage } from '../types'

interface AppHeaderProps {
  stage: Stage
  onStageChange: (stage: Stage) => void
  ingestCount: string
  reviewCount: string
  compileCount: string
  runStatus: RunStatus
}

const stages: Array<{ id: Stage; label: string }> = [
  { id: 'ingest', label: 'Ingest' },
  { id: 'review', label: 'Review' },
  { id: 'compile', label: 'Compile' },
]

export function AppHeader({ stage, onStageChange, ingestCount, reviewCount, compileCount, runStatus }: AppHeaderProps) {
  const counts = { ingest: ingestCount, review: reviewCount, compile: compileCount }
  return (
    <header className="app-header">
      <button className="brand" onClick={() => onStageChange('ingest')} aria-label="AutoPOROTW home">
        <span className="brand-mark"><Layers3 size={16} /></span>
        <span>AutoPOROTW</span>
      </button>

      <nav className="stage-nav" aria-label="Workflow stages">
        {stages.map((item, index) => (
          <button
            key={item.id}
            className={`stage-link ${stage === item.id ? 'active' : ''}`}
            onClick={() => onStageChange(item.id)}
            aria-current={stage === item.id ? 'page' : undefined}
          >
            <span className="stage-number">0{index + 1}</span>
            <span>{item.label}</span>
            <span className="stage-count">{counts[item.id]}</span>
          </button>
        ))}
      </nav>

      <div className={`run-indicator ${runStatus}`}>
        {runStatus === 'complete' ? <CheckCircle2 size={13} /> : <Activity size={13} />}
        <span>{runStatus === 'complete' ? 'Run complete' : runStatus}</span>
      </div>
    </header>
  )
}
