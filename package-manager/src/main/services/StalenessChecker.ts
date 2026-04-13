import { readFile, lstat, access } from 'fs/promises'
import { join } from 'path'
import { createHash } from 'crypto'

export type StalenessResult = 'current' | 'stale' | 'source-missing'

async function pathExists(p: string): Promise<boolean> {
  try {
    await access(p)
    return true
  } catch {
    return false
  }
}

async function hashFile(filePath: string): Promise<string> {
  const content = await readFile(filePath)
  return createHash('sha256').update(content).digest('hex')
}

/**
 * Checks if an installed resource matches its source.
 *
 * - Symlinks are always 'current' (they point to the live source)
 * - For file copies: compares SHA-256 hashes
 * - For directory copies: compares SKILL.md hash
 * - Returns 'source-missing' if source no longer exists
 */
export async function checkStaleness(
  installedPath: string,
  sourcePath: string
): Promise<StalenessResult> {
  // Check if source still exists
  if (!(await pathExists(sourcePath))) {
    return 'source-missing'
  }

  // Check if installed is a symlink — always current
  const stat = await lstat(installedPath)
  if (stat.isSymbolicLink()) {
    return 'current'
  }

  // For directories (skills), compare SKILL.md
  if (stat.isDirectory()) {
    const installedSkillMd = join(installedPath, 'SKILL.md')
    const sourceSkillMd = join(sourcePath, 'SKILL.md')

    if (!(await pathExists(installedSkillMd)) || !(await pathExists(sourceSkillMd))) {
      return 'stale'
    }

    const [installedHash, sourceHash] = await Promise.all([
      hashFile(installedSkillMd),
      hashFile(sourceSkillMd)
    ])

    return installedHash === sourceHash ? 'current' : 'stale'
  }

  // For files (agents, commands), compare full content hash
  const [installedHash, sourceHash] = await Promise.all([
    hashFile(installedPath),
    hashFile(sourcePath)
  ])

  return installedHash === sourceHash ? 'current' : 'stale'
}
