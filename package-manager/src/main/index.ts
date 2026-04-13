import { app, BrowserWindow, ipcMain } from 'electron'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { ConfigService, detectRepoPath } from './services/ConfigService'
import { StagingService } from './services/StagingService'
import { scanRepo } from './services/RepoScanner'
import { loadWorkflows } from './services/WorkflowService'
import { scanInstalled } from './services/InstalledScanner'
import { checkStaleness } from './services/StalenessChecker'
import { applyChanges } from './services/ChangeApplier'
import { IPC_CHANNELS } from '../shared/ipc-channels'
import type { PendingChange, RepoStatus, GitPullResult } from '../shared/types'
import { expandTilde } from './services/expandTilde'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// ---- Service instances ----
const configService = new ConfigService(
  path.join(app.getPath('userData'), 'config.json')
)
const stagingService = new StagingService()

// Auto-detect repo path if not configured
const config = configService.getConfig()
if (!config.repoPath) {
  const detected = detectRepoPath()
  if (detected) {
    configService.setConfig({ repoPath: detected })
  }
}

// ---- IPC handlers ----

ipcMain.handle(IPC_CHANNELS.GET_CONFIG, async () => {
  try {
    return configService.getConfig()
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.SET_CONFIG, async (_event, args) => {
  try {
    configService.setConfig(args)
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.SCAN_LIBRARY, async (_event, args) => {
  try {
    const repoPath = expandTilde(args.repoPath)
    return await scanRepo(repoPath)
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.SCAN_INSTALLED, async (_event, args) => {
  try {
    const targetDir = expandTilde(args.targetDir)
    const repoPath = expandTilde(args.repoPath)
    return await scanInstalled(targetDir, repoPath)
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.GET_WORKFLOWS, async (_event, args) => {
  try {
    const repoPath = expandTilde(args.repoPath)
    return await loadWorkflows(repoPath)
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.STAGE_CHANGE, async (_event, args) => {
  try {
    if (args.action === 'install') {
      stagingService.stageInstall(args, args.installMethod)
    } else if (args.action === 'remove') {
      stagingService.stageRemove(args)
    } else if (args.action === 'update') {
      stagingService.stageUpdate(args)
    }
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.UNSTAGE_CHANGE, async (_event, args) => {
  try {
    stagingService.unstage(args.id)
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.GET_STAGED, async () => {
  try {
    return stagingService.getChanges()
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.CLEAR_STAGED, async () => {
  try {
    stagingService.clearAll()
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.APPLY_CHANGES, async (_event, args) => {
  try {
    const expandedChanges = args.map((c: PendingChange) => ({
      ...c,
      sourcePath: expandTilde(c.sourcePath),
      targetPath: expandTilde(c.targetPath),
    }))
    const results = await applyChanges(expandedChanges)

    for (const result of results) {
      if (result.success) {
        stagingService.unstage(result.id)
      }
    }

    return results
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.CHECK_STALENESS, async (_event, args) => {
  try {
    return await checkStaleness(args.installedPath, args.sourcePath)
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.CHECK_REPO_STATUS, async (_event, args): Promise<RepoStatus> => {
  const cwd = expandTilde(args.repoPath)
  try {
    await execFileAsync('git', ['rev-parse', '--git-dir'], { cwd })
  } catch {
    return { isGitRepo: false, updatesAvailable: false }
  }
  try {
    await execFileAsync('git', ['fetch', '--quiet'], { cwd, timeout: 15000 })
    const { stdout } = await execFileAsync(
      'git',
      ['rev-list', '--count', 'HEAD..@{upstream}'],
      { cwd }
    )
    const behind = parseInt(stdout.trim(), 10) || 0
    return { isGitRepo: true, updatesAvailable: behind > 0, behindCount: behind }
  } catch (err) {
    return { isGitRepo: true, updatesAvailable: false, error: err instanceof Error ? err.message : String(err) }
  }
})

ipcMain.handle(IPC_CHANNELS.GIT_PULL, async (_event, args): Promise<GitPullResult> => {
  const cwd = expandTilde(args.repoPath)
  try {
    await execFileAsync('git', ['pull', '--ff-only'], { cwd, timeout: 30000 })
    return { success: true }
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
})

// ---- Window management ----

let mainWindow: BrowserWindow | null

const createWindow = (): void => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Arcanum Package Manager',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.cjs'),
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.on('ready', () => {
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})
