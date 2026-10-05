import type { Article, ArticleInput, Compilation, GuidelineHit, SimilarityMatch } from '../types'

const completeWorkflows = {
  embedding: { status: 'complete' as const, durationMs: 472 },
  similarity: { status: 'complete' as const, durationMs: 688 },
  llm: { status: 'complete' as const, durationMs: 1240 },
}

const hits: GuidelineHit[][] = [
  [{ id: 'G-01', label: 'Regulatory enforcement', confidence: 0.98, reason: 'References a regulator, financial penalty, and an enforcement outcome.' }],
  [{ id: 'G-07', label: 'Material cyber incident', confidence: 0.96, reason: 'Discloses a ransomware incident involving sensitive patient records.' }],
  [{ id: 'G-04', label: 'Strategic transaction', confidence: 0.91, reason: 'A material acquisition may change regional logistics concentration.' }],
  [{ id: 'G-09', label: 'Executive transition', confidence: 0.84, reason: 'Chief executive departure is tied to an active board review.' }],
  [],
  [{ id: 'G-07', label: 'Product liability', confidence: 0.89, reason: 'Litigation alleges a defect with potential customer harm.' }],
  [],
  [
    { id: 'G-02', label: 'Market integrity', confidence: 0.87, reason: 'A regulator opened an investigation into market disclosures.' },
    { id: 'G-09', label: 'Executive transition', confidence: 0.78, reason: 'The chief executive resigned during the investigation.' },
  ],
]

const rawArticles: Array<ArticleInput & { url: string; confidence: number; decision: Article['reviewDecision']; motherhood: Article['motherhoodResult'] }> = [
  {
    recordTitle: 'Regulator fines Northwind Bank $42M over anti-money-laundering lapses',
    recordContent: 'The national banking regulator fined Northwind Bank $42 million on Monday, citing persistent failures in its anti-money-laundering controls. The penalty follows a two-year review that found thousands of suspicious transactions went unreported.\n\nNorthwind said it accepted the findings and had already invested in new monitoring systems. Analysts said the enforcement action could delay the bank’s planned expansion into new markets.',
    recordSourceName: 'Financial Times', recordISOTimeStamp: '2026-09-28T08:30:00Z', url: 'https://example.com/northwind-fine', confidence: 0.84, decision: 'pending', motherhood: 'relevant',
  },
  {
    recordTitle: 'Helix Health confirms ransomware attack exposed 1.2M patient records',
    recordContent: 'Helix Health confirmed that an August ransomware attack exposed personal and clinical information belonging to approximately 1.2 million patients. The provider has begun notifying affected individuals and has engaged external incident-response specialists.\n\nOperations have returned to normal, but several regional authorities are reviewing the company’s security controls and disclosure timeline.',
    recordSourceName: 'Reuters', recordISOTimeStamp: '2026-09-29T11:10:00Z', url: 'https://example.com/helix-ransomware', confidence: 0.98, decision: 'relevant', motherhood: 'relevant',
  },
  {
    recordTitle: 'Orbital Logistics to buy FreightPath for $1.8 billion',
    recordContent: 'Orbital Logistics agreed to acquire FreightPath for about $1.8 billion, expanding its freight brokerage reach across North America. The deal, expected to close next year, is subject to regulatory approval.\n\nOrbital said the acquisition would add more than 4,000 shipper relationships to its network.',
    recordSourceName: 'Bloomberg', recordISOTimeStamp: '2026-09-30T14:05:00Z', url: 'https://example.com/orbital-freightpath', confidence: 0.99, decision: 'relevant', motherhood: 'relevant',
  },
  {
    recordTitle: 'Quarry Foods CEO steps down amid board review',
    recordContent: 'Quarry Foods said chief executive Mara Chen will step down immediately while the board reviews procurement practices in two business units. The company named its finance director interim chief executive.\n\nThe review is expected to conclude before year end and the company maintained its annual outlook.',
    recordSourceName: 'WSJ', recordISOTimeStamp: '2026-10-01T06:50:00Z', url: 'https://example.com/quarry-ceo', confidence: 0.71, decision: 'pending', motherhood: 'irrelevant',
  },
  {
    recordTitle: 'City council approves expanded bike lane network',
    recordContent: 'The city council approved a five-year plan to add 68 kilometres of protected bike lanes. Construction on the first phase will begin in January and will be funded through an existing transport levy.',
    recordSourceName: 'Metro Daily', recordISOTimeStamp: '2026-10-01T09:30:00Z', url: 'https://example.com/bike-lanes', confidence: 0.37, decision: 'irrelevant', motherhood: 'irrelevant',
  },
  {
    recordTitle: 'Class action lawsuit filed against Lumen Devices over battery defect',
    recordContent: 'Consumers filed a proposed class action against Lumen Devices alleging batteries in two laptop models can swell after extended use. Lumen said it is investigating the claims and has not issued a recall.\n\nThe filing seeks compensation and a court-supervised replacement programme.',
    recordSourceName: 'The Verge', recordISOTimeStamp: '2026-10-02T03:15:00Z', url: 'https://example.com/lumen-lawsuit', confidence: 0.64, decision: 'pending', motherhood: 'relevant',
  },
  {
    recordTitle: 'Arcadia Energy posts quarterly results above expectations',
    recordContent: 'Arcadia Energy reported quarterly revenue and profit above analyst expectations as higher industrial demand offset weaker retail volumes. The company reiterated its full-year capital expenditure guidance.',
    recordSourceName: 'CNBC', recordISOTimeStamp: '2026-10-02T12:45:00Z', url: 'https://example.com/arcadia-results', confidence: 0.43, decision: 'irrelevant', motherhood: 'irrelevant',
  },
  {
    recordTitle: 'Securities commission opens probe into Vantage Crypto; CEO resigns',
    recordContent: 'The securities commission opened an investigation into disclosures made by digital-asset platform Vantage Crypto. The company’s chief executive resigned hours after the inquiry was announced.\n\nVantage said customer assets remain available and that it intends to cooperate fully with investigators.',
    recordSourceName: 'CoinDesk', recordISOTimeStamp: '2026-10-03T17:20:00Z', url: 'https://example.com/vantage-probe', confidence: 0.57, decision: 'pending', motherhood: 'relevant',
  },
]

const comparisonTitles = [
  'Northwind Bank under scrutiny for anti-money-laundering controls',
  'Helix Health investigates ransomware attack',
  'Global shipping rates ease in third quarter',
]

function createMatches(index: number): SimilarityMatch[] {
  return comparisonTitles.map((title, matchIndex) => ({
    id: `match-${index}-${matchIndex}`,
    title,
    source: ['Financial Times', 'Reuters', 'WSJ'][matchIndex],
    score: Math.max(0.29, [0.839, 0.656, 0.342][matchIndex] - index * 0.025),
  }))
}

export function createArticleFromInput(input: ArticleInput, index: number, queued = false): Article {
  const confidence = rawArticles[index]?.confidence ?? Math.min(0.95, 0.42 + ((index * 17) % 48) / 100)
  return {
    id: `article-${Date.now()}-${index}`,
    sequence: index + 1,
    title: input.recordTitle.trim(),
    content: input.recordContent.trim(),
    source: input.recordSourceName?.trim() || 'Unknown source',
    sourceUrl: rawArticles[index]?.url,
    publishedAt: input.recordISOTimeStamp,
    wordCount: input.recordContent.trim().split(/\s+/).filter(Boolean).length,
    confidence,
    systemPrediction: confidence >= 0.5 ? 'relevant' : 'irrelevant',
    reviewDecision: queued ? 'pending' : (rawArticles[index]?.decision ?? 'pending'),
    reviewerNote: '',
    guidelineHits: hits[index] ?? [],
    motherhoodResult: rawArticles[index]?.motherhood ?? (confidence > 0.6 ? 'relevant' : 'irrelevant'),
    motherhoodReason: confidence > 0.6
      ? 'The article may materially affect public confidence, institutional risk, or stakeholder safety.'
      : 'No broad public-interest or institutional-risk signal was detected.',
    similarityMatches: createMatches(index),
    workflows: queued
      ? {
          embedding: { status: 'queued' },
          similarity: { status: 'queued' },
          llm: { status: 'queued' },
        }
      : completeWorkflows,
  }
}

export const demoInputs: ArticleInput[] = rawArticles.map(({ recordTitle, recordContent, recordSourceName, recordISOTimeStamp }) => ({
  recordTitle, recordContent, recordSourceName, recordISOTimeStamp,
}))

export const demoArticles: Article[] = demoInputs.map((input, index) => createArticleFromInput(input, index))

const now = new Date('2026-10-05T09:00:00+08:00').toISOString()

export const demoCompilations: Compilation[] = [
  {
    id: 'comp-current', title: 'Weekly Risk Briefing',
    introduction: 'Articles reviewed and marked relevant by the classification team, grouped for distribution.',
    articleIds: demoArticles.filter((article) => article.reviewDecision === 'relevant').map((article) => article.id),
    previewMode: 'lead', createdAt: now, updatedAt: now,
  },
  {
    id: 'comp-previous-1', title: 'Regulatory & Cyber Watch — Week 39',
    introduction: 'Priority regulatory, cyber, and corporate-governance developments for the weekly risk meeting.',
    articleIds: [demoArticles[0].id, demoArticles[1].id], previewMode: 'lead',
    createdAt: '2026-09-28T10:00:00+08:00', updatedAt: '2026-09-29T16:20:00+08:00',
  },
  {
    id: 'comp-previous-2', title: 'September Strategic Transactions Digest',
    introduction: 'Material transactions and leadership changes observed across monitored sources.',
    articleIds: [demoArticles[2].id, demoArticles[3].id], previewMode: 'full',
    createdAt: '2026-09-20T10:00:00+08:00', updatedAt: '2026-09-25T14:35:00+08:00',
  },
]
