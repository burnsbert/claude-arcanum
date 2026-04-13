import { readdir, lstat, realpath } from 'fs/promises'
import { join, relative, basename } from 'path'
import type { InstalledResource } from '@shared/types'

const RESOURCE_DIRS: Array<{ dir: string; type: 'agent' | 'command' | 'skill' }> = [
  { dir: 'agents', type: 'agent' },
  { dir: 'commands', type: 'command' },
  { dir: 'skills', type: 'skill' }
]

/**
 * Extract a repo name from a resolved symlink path.
 * Looks for a known resource-type directory in the path and takes
 * the directory just before it as the repo name.
 */
function extractRepoName(resolvedPath: string): string {
  const parts = resolvedPath.split('/')
  const resourceDirNames = new Set(['agents', 'commands', 'skills'])

  for (let i = parts.length - 1; i >= 0; i--) {
    if (resourceDirNames.has(parts[i]) && i > 0) {
      return parts[i - 1]
    }
  }

  const parentIndex = parts.length - 2
  if (parentIndex >= 0 && parts[parentIndex]) {
    return parts[parentIndex]
  }

  return 'unknown'
}

async function dirExists(dirPath: string): Promise<boolean> {
  try {
    const stat = await lstat(dirPath)
    return stat.isDirectory()
  } catch {
    return false
  }
}

/**
 * Classify a single installed item.
 */
async function classifyResource(
  itemPath: string,
  name: string,
  type: 'agent' | 'command' | 'skill',
  arcanumRoot: string
): Promise<InstalledResource> {
  const stat = await lstat(itemPath)

  if (stat.isSymbolicLink()) {
    let resolvedTarget: string | undefined
    let source: string
    let repoPath: string | undefined

    try {
      resolvedTarget = await realpath(itemPath)

      const normalizedResolved = resolvedTarget
      const normalizedRoot = arcanumRoot.endsWith('/')
        ? arcanumRoot
        : arcanumRoot + '/'

      if (normalizedResolved.startsWith(normalizedRoot) || normalizedResolved === arcanumRoot) {
        source = 'arcanum'
        repoPath = relative(arcanumRoot, normalizedResolved)
      } else {
        const repoName = extractRepoName(resolvedTarget)
        source = `other-repo:${repoName}`
      }
    } catch {
      source = 'broken-symlink'
      resolvedTarget = undefined
    }

    return {
      name,
      type,
      installType: 'symlink',
      source,
      repoPath,
      resolvedTarget,
      installedPath: itemPath
    }
  }

  return {
    name,
    type,
    installType: 'copy',
    source: 'local',
    installedPath: itemPath
  }
}

/**
 * Scan ~/.claude for installed resources and classify each one
 * by install type, source, and arcanum association.
 */
export async function scanInstalled(
  targetDir: string,
  arcanumRoot: string
): Promise<InstalledResource[]> {
  if (!(await dirExists(targetDir))) {
    return []
  }

  let resolvedRoot: string
  try {
    resolvedRoot = await realpath(arcanumRoot)
  } catch {
    resolvedRoot = arcanumRoot
  }

  const results: InstalledResource[] = []

  for (const { dir, type } of RESOURCE_DIRS) {
    const subDir = join(targetDir, dir)

    if (!(await dirExists(subDir))) {
      continue
    }

    const entries = await readdir(subDir, { withFileTypes: true })

    for (const entry of entries) {
      const itemPath = join(subDir, entry.name)

      if (type === 'skill') {
        const itemStat = await lstat(itemPath)
        if (itemStat.isSymbolicLink() || itemStat.isDirectory()) {
          const resource = await classifyResource(itemPath, entry.name, type, resolvedRoot)
          results.push(resource)
        }
      } else {
        if (!entry.name.endsWith('.md')) {
          continue
        }

        const name = basename(entry.name, '.md')
        const resource = await classifyResource(itemPath, name, type, resolvedRoot)
        results.push(resource)
      }
    }
  }

  return results
}
