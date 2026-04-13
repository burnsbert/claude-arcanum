import { describe, it, expect } from 'vitest'
import { scanRepo } from './RepoScanner'
import { resolve } from 'path'

const REPO_ROOT = resolve(__dirname, '..', '..', '..', '..')

describe('RepoScanner integration', () => {
  it('scans the actual arcanum repo', async () => {
    const plugin = await scanRepo(REPO_ROOT)

    expect(plugin.id).toBe('arcanum')
    expect(plugin.name).toBe('arcanum')
    expect(plugin.version).toMatch(/^\d+\.\d+\.\d+$/)

    // Agents: expect at least 25 (currently 30)
    expect(plugin.agents.length).toBeGreaterThanOrEqual(25)

    // Commands: expect at least 8 (currently 9 after pr-review/pr-respond moved to skills)
    expect(plugin.commands.length).toBeGreaterThanOrEqual(8)

    // Skills: expect at least 3 (rubber-duck, arc-pr-review, arc-pr-respond)
    expect(plugin.skills.length).toBeGreaterThanOrEqual(3)

    // Verify a known agent has proper metadata
    const brainstormer = plugin.agents.find(a => a.name === 'ca-brainstormer')
    expect(brainstormer).toBeDefined()
    expect(brainstormer!.description).toContain('theory')
    expect(brainstormer!.color).toBe('blue')

    // Verify a known command
    const investigate = plugin.commands.find(c => c.name === 'arc-investigate')
    expect(investigate).toBeDefined()

    // Verify arc-rubber-duck skill
    const rubberDuck = plugin.skills.find(s => s.name === 'arc-rubber-duck')
    expect(rubberDuck).toBeDefined()
    expect(rubberDuck!.userInvocable).toBe(true)
    expect(rubberDuck!.dirPath).toContain('skills/arc-rubber-duck')

    // Verify arc-pr-review skill (converted from command)
    const prReview = plugin.skills.find(s => s.name === 'arc-pr-review')
    expect(prReview).toBeDefined()
    expect(prReview!.userInvocable).toBe(true)
    expect(prReview!.dirPath).toContain('skills/arc-pr-review')

    // Verify personalities/ subdirectory is excluded
    const hasPersonality = plugin.agents.some(a => a.name.includes('contrarian') || a.name.includes('pragmatist'))
    expect(hasPersonality).toBe(false)
  })
})
