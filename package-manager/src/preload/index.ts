import { contextBridge, ipcRenderer } from 'electron'
import { IPC_CHANNELS } from '../shared/ipc-channels'
import type {
  AppConfig,
  Plugin,
  InstalledResource,
  Workflow,
  PendingChange,
  ApplyResult,
  RepoStatus,
  GitPullResult,
} from '../shared/types'

const api = {
  getConfig: (): Promise<AppConfig> =>
    ipcRenderer.invoke(IPC_CHANNELS.GET_CONFIG),

  setConfig: (config: Partial<AppConfig>): Promise<void> =>
    ipcRenderer.invoke(IPC_CHANNELS.SET_CONFIG, config),

  scanLibrary: (repoPath: string): Promise<Plugin> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCAN_LIBRARY, { repoPath }),

  scanInstalled: (targetDir: string, repoPath: string): Promise<InstalledResource[]> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCAN_INSTALLED, { targetDir, repoPath }),

  getWorkflows: (repoPath: string): Promise<Workflow[]> =>
    ipcRenderer.invoke(IPC_CHANNELS.GET_WORKFLOWS, { repoPath }),

  stageChange: (change: Omit<PendingChange, 'id'>): Promise<void> =>
    ipcRenderer.invoke(IPC_CHANNELS.STAGE_CHANGE, change),

  unstageChange: (id: string): Promise<void> =>
    ipcRenderer.invoke(IPC_CHANNELS.UNSTAGE_CHANGE, { id }),

  getStagedChanges: (): Promise<PendingChange[]> =>
    ipcRenderer.invoke(IPC_CHANNELS.GET_STAGED),

  clearStaged: (): Promise<void> =>
    ipcRenderer.invoke(IPC_CHANNELS.CLEAR_STAGED),

  applyChanges: (changes: PendingChange[]): Promise<ApplyResult[]> =>
    ipcRenderer.invoke(IPC_CHANNELS.APPLY_CHANGES, changes),

  checkStaleness: (installedPath: string, sourcePath: string): Promise<'current' | 'stale' | 'source-missing'> =>
    ipcRenderer.invoke(IPC_CHANNELS.CHECK_STALENESS, { installedPath, sourcePath }),

  checkRepoStatus: (repoPath: string): Promise<RepoStatus> =>
    ipcRenderer.invoke(IPC_CHANNELS.CHECK_REPO_STATUS, { repoPath }),

  gitPull: (repoPath: string): Promise<GitPullResult> =>
    ipcRenderer.invoke(IPC_CHANNELS.GIT_PULL, { repoPath }),
}

contextBridge.exposeInMainWorld('api', api)

export type ApiType = typeof api
