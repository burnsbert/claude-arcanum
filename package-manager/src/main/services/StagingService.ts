import { randomUUID } from 'crypto'
import type { PendingChange } from '@shared/types'

/**
 * In-memory staging service for pending filesystem changes.
 * Changes are queued here and applied together when the user confirms.
 */
export class StagingService {
  private changes: PendingChange[] = []

  /** Stage an install action. Idempotent — duplicate targetPaths are silently ignored. */
  stageInstall(change: Omit<PendingChange, 'id'>, method: 'symlink' | 'copy'): void {
    if (this.changes.some(c => c.targetPath === change.targetPath)) return
    this.changes.push({
      ...change,
      id: randomUUID(),
      action: 'install',
      installMethod: method,
    })
  }

  /** Stage a remove action. Idempotent. */
  stageRemove(change: Omit<PendingChange, 'id'>): void {
    if (this.changes.some(c => c.targetPath === change.targetPath)) return
    this.changes.push({
      ...change,
      id: randomUUID(),
      action: 'remove',
    })
  }

  /** Stage an update action. Idempotent. */
  stageUpdate(change: Omit<PendingChange, 'id'>): void {
    if (this.changes.some(c => c.targetPath === change.targetPath)) return
    this.changes.push({
      ...change,
      id: randomUUID(),
      action: 'update',
    })
  }

  /** Remove a staged change by ID. */
  unstage(id: string): void {
    this.changes = this.changes.filter(c => c.id !== id)
  }

  /** Return a shallow copy of all pending changes. */
  getChanges(): PendingChange[] {
    return [...this.changes]
  }

  /** Clear all staged changes. */
  clearAll(): void {
    this.changes = []
  }

  /** Return the count of pending changes. */
  getCount(): number {
    return this.changes.length
  }
}
