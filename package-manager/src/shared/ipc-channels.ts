/**
 * Shared IPC channel constants and request/response types
 */
import type {
  AppConfig,
  Plugin,
  InstalledResource,
  Workflow,
  PendingChange,
  ApplyResult,
} from './types'

export const IPC_CHANNELS = {
  SCAN_LIBRARY: 'scan-library',
  SCAN_INSTALLED: 'scan-installed',
  GET_CONFIG: 'get-config',
  SET_CONFIG: 'set-config',
  APPLY_CHANGES: 'apply-changes',
  GET_WORKFLOWS: 'get-workflows',
  STAGE_CHANGE: 'stage-change',
  UNSTAGE_CHANGE: 'unstage-change',
  GET_STAGED: 'get-staged',
  CLEAR_STAGED: 'clear-staged',
  CHECK_STALENESS: 'check-staleness',
  CHECK_REPO_STATUS: 'check-repo-status',
  GIT_PULL: 'git-pull',
} as const

/**
 * IPC Request/Response type mappings
 */
export interface IpcChannelMap {
  [IPC_CHANNELS.GET_CONFIG]: {
    request: undefined
    response: AppConfig
  }

  [IPC_CHANNELS.SET_CONFIG]: {
    request: Partial<AppConfig>
    response: void
  }

  [IPC_CHANNELS.SCAN_LIBRARY]: {
    request: {
      repoPath: string
    }
    response: Plugin
  }

  [IPC_CHANNELS.SCAN_INSTALLED]: {
    request: {
      targetDir: string
      repoPath: string
    }
    response: InstalledResource[]
  }

  [IPC_CHANNELS.GET_WORKFLOWS]: {
    request: {
      repoPath: string
    }
    response: Workflow[]
  }

  [IPC_CHANNELS.STAGE_CHANGE]: {
    request: Omit<PendingChange, 'id'>
    response: void
  }

  [IPC_CHANNELS.UNSTAGE_CHANGE]: {
    request: {
      id: string
    }
    response: void
  }

  [IPC_CHANNELS.GET_STAGED]: {
    request: undefined
    response: PendingChange[]
  }

  [IPC_CHANNELS.CLEAR_STAGED]: {
    request: undefined
    response: void
  }

  [IPC_CHANNELS.APPLY_CHANGES]: {
    request: PendingChange[]
    response: ApplyResult[]
  }

  [IPC_CHANNELS.CHECK_STALENESS]: {
    request: {
      installedPath: string
      sourcePath: string
    }
    response: 'current' | 'stale' | 'source-missing'
  }
}
