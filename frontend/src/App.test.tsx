import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('AutoPOROTW prototype', () => {
  it('shows a validation error for invalid pasted JSON', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /New run/i }))
    await user.click(screen.getByRole('button', { name: /Paste JSON/i }))
    const editor = screen.getByRole('textbox', { name: /Article JSON/i })
    fireEvent.change(editor, { target: { value: '{bad json' } })
    await user.click(screen.getByRole('button', { name: /Start ingest/i }))

    expect(screen.getByRole('alert')).toHaveTextContent('not valid JSON')
  })

  it('can start, pause, and resume a demo ingest run', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /New run/i }))
    await user.click(screen.getByRole('button', { name: /Load demo batch/i }))
    expect(screen.getByRole('button', { name: /Pause/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Pause/i }))
    expect(screen.getByRole('button', { name: /Resume/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Resume/i }))
    expect(screen.getByRole('button', { name: /Pause/i })).toBeInTheDocument()
  })

  it('adds a relevant review decision to the active compilation', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /Review.*4 pending/i }))
    expect(screen.getByRole('heading', { name: /Regulator fines Northwind/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /^Relevant.*R$/i }))

    expect(screen.getByRole('button', { name: /Compile.*3 in doc/i })).toBeInTheDocument()
  })

  it('opens compilation history and provides visual-only export feedback', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /Compile.*2 in doc/i }))
    await user.click(screen.getByRole('button', { name: /History.*3/i }))
    expect(screen.getByRole('button', { name: /Regulatory & Cyber Watch/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /PDF/i }))
    expect(screen.getByRole('status')).toHaveTextContent('PDF export is visual-only')
  })

  it('duplicates an editable compilation', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: /Compile.*2 in doc/i }))
    await user.click(screen.getByRole('button', { name: /Duplicate/i }))
    expect(screen.getByRole('status')).toHaveTextContent('Compilation duplicated')
    expect(screen.getByDisplayValue(/Weekly Risk Briefing — Copy/i)).toBeInTheDocument()
  })
})
