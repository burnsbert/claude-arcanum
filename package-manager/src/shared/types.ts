/**
 * Shared TypeScript types for main process, preload, and renderer
 */

export interface Plugin {
  id: string
  name: string
  version: string
  description: string
  agents: Agent[]
  commands: Command[]
  skills: Skill[]
}

export interface Agent {
  name: string
  description: string
  model?: string
  tools?: string[]
  color?: string
  sourcePath?: string
  lastUpdated?: string
}

export interface Command {
  name: string
  description: string
  allowedTools?: string[]
  argumentHint?: string
  lastUpdated?: string
}

export interface Skill {
  name: string
  description: string
  allowedTools?: string[]
  userInvocable?: boolean
  argumentHint?: string
  dirPath?: string
  lastUpdated?: string
}

export interface InstalledResource {
  name: string
  type: 'agent' | 'command' | 'skill'
  installType: 'symlink' | 'copy' | 'unknown'
  source: string
  repoPath?: string
  resolvedTarget?: string
  installedPath?: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  icon: string
  members: WorkflowMember[]
  lastUpdated?: string
}

export interface WorkflowMember {
  path: string
  type: 'agent' | 'command' | 'skill'
  name: string
  standalone?: boolean
  description?: string
}

export interface PendingChange {
  id: string
  action: 'install' | 'remove' | 'update'
  resourceType: 'agent' | 'command' | 'skill'
  resourceName: string
  sourcePath: string
  targetPath: string
  installMethod: 'symlink' | 'copy'
}

export interface AppConfig {
  repoPath: string
  defaultInstallMethod: 'symlink' | 'copy'
  theme: 'light' | 'dark' | 'system'
}

export interface ApplyResult {
  id: string
  success: boolean
  error?: string
}

export type InstallStatus = 'installed-symlink' | 'installed-copy' | 'update-available' | 'not-installed' | 'orphaned'

export interface RepoStatus {
  isGitRepo: boolean
  updatesAvailable: boolean
  behindCount?: number
  error?: string
}

export interface GitPullResult {
  success: boolean
  error?: string
}
