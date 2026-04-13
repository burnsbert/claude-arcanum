import { lstat } from 'fs/promises'
import type { PendingChange, ApplyResult } from '@shared/types'
import { createSymlink, copyFile, copyDirectory, removeResource } from './FileOperations'

/**
 * Performs the install step of a pending change.
 */
async function applyInstall(change: PendingChange): Promise<void> {
  if (change.installMethod === 'symlink') {
    await createSymlink(change.sourcePath, change.targetPath)
  } else {
    const stat = await lstat(change.sourcePath)
    if (stat.isDirectory()) {
      await copyDirectory(change.sourcePath, change.targetPath)
    } else {
      await copyFile(change.sourcePath, change.targetPath)
    }
  }
}

/**
 * Applies a list of staged PendingChanges sequentially.
 * Individual failures are captured and do NOT abort remaining changes.
 */
export async function applyChanges(changes: PendingChange[]): Promise<ApplyResult[]> {
  const results: ApplyResult[] = []

  for (const change of changes) {
    try {
      if (change.action === 'install') {
        await applyInstall(change)
      } else if (change.action === 'remove') {
        await removeResource(change.targetPath)
      } else if (change.action === 'update') {
        await removeResource(change.targetPath)
        await applyInstall(change)
      }

      results.push({ id: change.id, success: true })
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      results.push({ id: change.id, success: false, error: message })
    }
  }

  return results
}
