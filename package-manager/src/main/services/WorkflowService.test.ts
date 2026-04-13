import { describe, it, expect } from 'vitest'
import { loadWorkflows } from './WorkflowService'
import { resolve } from 'path'

const REPO_ROOT = resolve(__dirname, '..', '..', '..', '..')

describe('WorkflowService integration', () => {
  it('loads workflows from the actual repo', async () => {
    const workflows = await loadWorkflows(REPO_ROOT)

    // Expect 9 workflows
    expect(workflows.length).toBe(9)

    // Verify known workflows exist
    const ids = workflows.map(w => w.id)
    expect(ids).toContain('investigate')
    expect(ids).toContain('maestro')
    expect(ids).toContain('pr-review')
    expect(ids).toContain('think-tank')

    // Verify maestro has the most members
    const maestro = workflows.find(w => w.id === 'maestro')!
    expect(maestro.members.length).toBeGreaterThanOrEqual(14)

    // Verify member types are inferred correctly
    const investigateWf = workflows.find(w => w.id === 'investigate')!
    const commands = investigateWf.members.filter(m => m.type === 'command')
    const agents = investigateWf.members.filter(m => m.type === 'agent')
    expect(commands.length).toBeGreaterThanOrEqual(1)
    expect(agents.length).toBeGreaterThanOrEqual(2)

    // Verify lastUpdated is computed
    for (const workflow of workflows) {
      expect(workflow.lastUpdated).toBeDefined()
    }
  })

  it('returns empty for nonexistent path', async () => {
    const workflows = await loadWorkflows('/nonexistent/path')
    expect(workflows).toEqual([])
  })
})
