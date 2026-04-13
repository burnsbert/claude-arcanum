import { describe, it, expect, beforeEach } from 'vitest'
import { StagingService } from './StagingService'

describe('StagingService', () => {
  let service: StagingService

  beforeEach(() => {
    service = new StagingService()
  })

  it('starts with no changes', () => {
    expect(service.getChanges()).toEqual([])
    expect(service.getCount()).toBe(0)
  })

  it('stages an install', () => {
    service.stageInstall({
      action: 'install',
      resourceType: 'agent',
      resourceName: 'test-agent',
      sourcePath: '/repo/agents/test-agent.md',
      targetPath: '~/.claude/agents/test-agent.md',
      installMethod: 'symlink',
    }, 'symlink')

    const changes = service.getChanges()
    expect(changes).toHaveLength(1)
    expect(changes[0].action).toBe('install')
    expect(changes[0].resourceName).toBe('test-agent')
    expect(changes[0].id).toBeTruthy()
  })

  it('is idempotent for same targetPath', () => {
    const change = {
      action: 'install' as const,
      resourceType: 'agent' as const,
      resourceName: 'test-agent',
      sourcePath: '/repo/agents/test-agent.md',
      targetPath: '~/.claude/agents/test-agent.md',
      installMethod: 'symlink' as const,
    }

    service.stageInstall(change, 'symlink')
    service.stageInstall(change, 'symlink')

    expect(service.getCount()).toBe(1)
  })

  it('unstages by id', () => {
    service.stageInstall({
      action: 'install',
      resourceType: 'agent',
      resourceName: 'test-agent',
      sourcePath: '/repo/agents/test-agent.md',
      targetPath: '~/.claude/agents/test-agent.md',
      installMethod: 'symlink',
    }, 'symlink')

    const id = service.getChanges()[0].id
    service.unstage(id)

    expect(service.getCount()).toBe(0)
  })

  it('clears all changes', () => {
    service.stageInstall({
      action: 'install',
      resourceType: 'agent',
      resourceName: 'agent1',
      sourcePath: '/repo/agents/agent1.md',
      targetPath: '~/.claude/agents/agent1.md',
      installMethod: 'symlink',
    }, 'symlink')

    service.stageRemove({
      action: 'remove',
      resourceType: 'command',
      resourceName: 'cmd1',
      sourcePath: '/repo/commands/cmd1.md',
      targetPath: '~/.claude/commands/cmd1.md',
      installMethod: 'symlink',
    })

    expect(service.getCount()).toBe(2)
    service.clearAll()
    expect(service.getCount()).toBe(0)
  })

  it('returns a shallow copy of changes', () => {
    service.stageInstall({
      action: 'install',
      resourceType: 'agent',
      resourceName: 'test',
      sourcePath: '/a',
      targetPath: '/b',
      installMethod: 'symlink',
    }, 'symlink')

    const changes1 = service.getChanges()
    const changes2 = service.getChanges()
    expect(changes1).not.toBe(changes2)
    expect(changes1).toEqual(changes2)
  })
})
