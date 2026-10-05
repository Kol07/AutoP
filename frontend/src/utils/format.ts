export function formatDuration(milliseconds: number) {
  if (milliseconds < 1000) return `${Math.round(milliseconds)}ms`
  return `${(milliseconds / 1000).toFixed(1)}s`
}

export function formatDate(value?: string, includeTime = false) {
  if (!value) return 'Date unavailable'
  return new Intl.DateTimeFormat('en-SG', {
    day: '2-digit', month: 'short', year: 'numeric',
    ...(includeTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  }).format(new Date(value))
}

export function getLead(content: string) {
  const firstParagraph = content.split(/\n\s*\n/)[0]
  return firstParagraph.length > 280 ? `${firstParagraph.slice(0, 277)}…` : firstParagraph
}

export function confidenceLabel(value: number) {
  if (value >= 0.8) return 'High confidence'
  if (value >= 0.5) return 'Medium confidence'
  return 'Low confidence'
}
