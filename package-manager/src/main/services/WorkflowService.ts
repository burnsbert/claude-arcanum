import { readFile, stat } from 'fs/promises'
import { join, basename, dirname } from 'path'
import type { Workflow, WorkflowMember } from '@shared/types'

/** Raw member entry from workflows.json */
interface RawMember {
  path: string
  type?: string
  name?: string
  standalone?: boolean
  description?: string
}

/** Raw workflow entry from workflows.json */
interface RawWorkflow {
  id: string
  name: string
  description: string
  icon: string
  members?: RawMember[]
}

/** Raw structure of workflows.json */
interface WorkflowsJson {
  workflows: RawWorkflow[]
}

/**
 * Infers the resource type from its path segment.
 */
function inferMemberType(path: string, explicitType?: string): 'agent' | 'command' | 'skill' {
  if (path.includes('/agents/')) return 'agent'
  if (path.includes('/commands/')) return 'command'
  if (path.includes('/skills/')) return 'skill'

  if (explicitType === 'agent' || explicitType === 'command' || explicitType === 'skill') {
    return explicitType
  }

  return 'agent'
}

/**
 * Infers the member display name from its path.
 */
function inferMemberName(path: string, type: 'agent' | 'command' | 'skill'): string {
  if (type === 'skill') {
    return basename(dirname(path))
  }
  return basename(path, '.md')
}

/**
 * Converts a raw member entry into a typed WorkflowMember.
 */
function resolveRawMember(raw: RawMember): WorkflowMember {
  const type = inferMemberType(raw.path, raw.type)
  const name = raw.name ?? inferMemberName(raw.path, type)

  const member: WorkflowMember = { path: raw.path, type, name }

  if (raw.standalone === true) member.standalone = true
  if (type !== 'agent' && typeof raw.description === 'string') {
    member.description = raw.description
  }

  return member
}

/**
 * Gets the file path for stat purposes.
 * Skill directory paths get SKILL.md appended.
 */
function getMemberFilePath(memberPath: string, repoPath: string): string {
  const resolved = join(repoPath, memberPath)
  if (!memberPath.includes('.')) {
    return join(resolved, 'SKILL.md')
  }
  return resolved
}

/**
 * Computes the max mtime across all member files.
 */
async function computeWorkflowLastUpdated(
  members: WorkflowMember[],
  repoPath: string
): Promise<string | undefined> {
  const mtimes = await Promise.all(
    members.map(async member => {
      try {
        const filePath = getMemberFilePath(member.path, repoPath)
        const fileStat = await stat(filePath)
        return fileStat.mtime.getTime()
      } catch {
        return null
      }
    })
  )

  const validMtimes = mtimes.filter((t): t is number => t !== null)
  if (validMtimes.length === 0) return undefined

  const maxTime = Math.max(...validMtimes)
  return new Date(maxTime).toISOString()
}

/**
 * Reads and parses workflows.json.
 */
async function readWorkflowsJson(repoPath: string): Promise<WorkflowsJson | null> {
  const filePath = join(repoPath, 'workflows.json')
  try {
    const content = await readFile(filePath, 'utf-8')
    const parsed = JSON.parse(content) as WorkflowsJson
    if (!Array.isArray(parsed.workflows)) return null
    return parsed
  } catch {
    return null
  }
}

/**
 * Loads all workflows from workflows.json in the repo root.
 * No mode filtering — all members are used directly.
 */
export async function loadWorkflows(repoPath: string): Promise<Workflow[]> {
  const data = await readWorkflowsJson(repoPath)
  if (!data) return []

  const workflows = await Promise.all(
    data.workflows.map(async (raw): Promise<Workflow> => {
      const members: WorkflowMember[] = (raw.members ?? []).map(resolveRawMember)
      const lastUpdated = await computeWorkflowLastUpdated(members, repoPath)

      const workflow: Workflow = {
        id: raw.id,
        name: raw.name,
        description: raw.description,
        icon: raw.icon,
        members
      }

      if (lastUpdated !== undefined) workflow.lastUpdated = lastUpdated

      return workflow
    })
  )

  return workflows.filter(w => w.members.length > 0)
}

/**
 * Returns a Set of all resource paths that belong to any workflow.
 */
export async function getWorkflowMemberPaths(repoPath: string): Promise<Set<string>> {
  const workflows = await loadWorkflows(repoPath)
  const paths = new Set<string>()
  for (const workflow of workflows) {
    for (const member of workflow.members) {
      paths.add(member.path)
    }
  }
  return paths
}
