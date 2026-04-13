import { create } from 'zustand'
import type {
  Agent,
  AppConfig,
  Command,
  Plugin,
  InstalledResource,
  Skill,
  Workflow,
  PendingChange,
} from '../../shared/types'
import type { ToastItem, ToastType } from '../components/Toast'

type ActiveSection = 'workflows' | 'skills' | 'commands' | 'agents' | 'settings' | 'review'

/** Maps an installed resource key ("name:type") to its staleness result */
type StalenessMap = Record<string, 'current' | 'stale' | 'source-missing'>

interface AppState {
  config: AppConfig | null
  plugin: Plugin | null
  installedResources: InstalledResource[]
  workflows: Workflow[]
  stagedChanges: PendingChange[]
  showNonArcanum: boolean
  darkMode: boolean
  activeSection: ActiveSection
  isLoading: boolean
  error: string | null
  toasts: ToastItem[]
  stalenessMap: StalenessMap
  searchQuery: string
  sortMode: 'recent' | 'name'

  initialize(): Promise<void>
  rescan(): Promise<void>
  stageChange(change: Omit<PendingChange, 'id'>): Promise<void>
  unstageChange(id: string): Promise<void>
  batchUnstage(ids: string[]): Promise<void>
  clearStaged(): Promise<void>
  applyChanges(): Promise<void>
  setActiveSection(section: ActiveSection): void
  toggleNonArcanum(): void
  toggleDarkMode(): void
  setError(error: string): void
  clearError(): void
  addToast(message: string, type: ToastType): void
  removeToast(id: string): void
  setSearchQuery(query: string): void
  setSortMode(mode: 'recent' | 'name'): void
}

function applyDarkModeClass(dark: boolean): void {
  if (dark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

let _systemThemeListener: ((e: MediaQueryListEvent) => void) | null = null

export function startSystemThemeListener(): void {
  stopSystemThemeListener()
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  _systemThemeListener = (e: MediaQueryListEvent) => {
    const dark = e.matches
    useAppStore.setState({ darkMode: dark })
    applyDarkModeClass(dark)
  }
  mq.addEventListener('change', _systemThemeListener)
}

export function stopSystemThemeListener(): void {
  if (_systemThemeListener) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.removeEventListener('change', _systemThemeListener)
    _systemThemeListener = null
  }
}

/** Browser-safe path join */
function joinPath(...segments: string[]): string {
  return segments.join('/').replace(/\/+/g, '/')
}

/** Build the source path in the repo for a resource */
export function buildSourcePath(
  repoPath: string,
  type: 'agent' | 'command' | 'skill',
  resource: Agent | Command | Skill
): string {
  if (type === 'skill') {
    const skill = resource as Skill
    if (skill.dirPath) return skill.dirPath
    return joinPath(repoPath, 'skills', resource.name)
  }

  const section = type === 'agent' ? 'agents' : 'commands'
  return joinPath(repoPath, section, `${resource.name}.md`)
}

/** Check staleness for all copy-installed resources */
async function checkAllStaleness(
  installedResources: InstalledResource[],
  availableResources: Array<{ name: string; type: 'agent' | 'command' | 'skill'; resource: Agent | Command | Skill }>,
  repoPath: string
): Promise<StalenessMap> {
  const copyInstalled = installedResources.filter((r) => r.installType === 'copy' && r.installedPath)

  if (copyInstalled.length === 0) return {}

  const availableByKey = new Map<string, Agent | Command | Skill>()
  for (const item of availableResources) {
    availableByKey.set(`${item.name}:${item.type}`, item.resource)
  }

  const results: StalenessMap = {}
  const checks = copyInstalled
    .map((installed) => {
      const key = `${installed.name}:${installed.type}`
      const available = availableByKey.get(key)
      if (!available || !installed.installedPath) return null
      const sourcePath = buildSourcePath(repoPath, installed.type, available)
      return { key, installedPath: installed.installedPath, sourcePath }
    })
    .filter(Boolean) as Array<{ key: string; installedPath: string; sourcePath: string }>

  const checkResults = await Promise.all(
    checks.map(async (check) => {
      try {
        const result = await window.api.checkStaleness(check.installedPath, check.sourcePath)
        return { key: check.key, result }
      } catch {
        return { key: check.key, result: 'current' as const }
      }
    })
  )

  for (const { key, result } of checkResults) {
    results[key] = result
  }

  return results
}

export const useAppStore = create<AppState>((set, get) => ({
  config: null,
  plugin: null,
  installedResources: [],
  workflows: [],
  stagedChanges: [],
  showNonArcanum: false,
  darkMode: false,
  activeSection: 'workflows',
  isLoading: false,
  error: null,
  toasts: [],
  stalenessMap: {},
  searchQuery: '',
  sortMode: (localStorage.getItem('sortMode') as 'recent' | 'name') || 'recent',

  initialize: async () => {
    set({ isLoading: true, error: null })
    try {
      const config = await window.api.getConfig()
      set({ config })

      if (!config.repoPath) {
        set({ isLoading: false, error: 'Repo path not configured. Check settings.' })
        return
      }

      // Apply theme
      if (config.theme === 'dark') {
        stopSystemThemeListener()
        set({ darkMode: true })
        applyDarkModeClass(true)
      } else if (config.theme === 'light') {
        stopSystemThemeListener()
        set({ darkMode: false })
        applyDarkModeClass(false)
      } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        set({ darkMode: prefersDark })
        applyDarkModeClass(prefersDark)
        startSystemThemeListener()
      }

      await get().rescan()
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
        isLoading: false,
      })
    }
  },

  rescan: async () => {
    set({ isLoading: true, error: null })
    try {
      const { config } = get()
      if (!config?.repoPath) {
        set({ isLoading: false })
        return
      }

      const [plugin, installedResources, workflows] = await Promise.all([
        window.api.scanLibrary(config.repoPath),
        window.api.scanInstalled('~/.claude', config.repoPath),
        window.api.getWorkflows(config.repoPath),
      ])

      const availableFlat = [
        ...plugin.agents.map((a) => ({ name: a.name, type: 'agent' as const, resource: a })),
        ...plugin.commands.map((c) => ({ name: c.name, type: 'command' as const, resource: c })),
        ...plugin.skills.map((s) => ({ name: s.name, type: 'skill' as const, resource: s })),
      ]

      const stalenessMap = await checkAllStaleness(
        installedResources,
        availableFlat,
        config.repoPath
      )

      set({
        plugin,
        installedResources,
        workflows,
        stalenessMap,
        isLoading: false,
      })
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
        isLoading: false,
      })
    }
  },

  stageChange: async (change: Omit<PendingChange, 'id'>) => {
    try {
      await window.api.stageChange(change)
      const stagedChanges = await window.api.getStagedChanges()
      set({ stagedChanges })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : String(err) })
    }
  },

  unstageChange: async (id: string) => {
    try {
      await window.api.unstageChange(id)
      const stagedChanges = await window.api.getStagedChanges()
      set({ stagedChanges })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : String(err) })
    }
  },

  batchUnstage: async (ids: string[]) => {
    try {
      for (const id of ids) {
        await window.api.unstageChange(id)
      }
      const stagedChanges = await window.api.getStagedChanges()
      set({ stagedChanges })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : String(err) })
    }
  },

  clearStaged: async () => {
    try {
      await window.api.clearStaged()
      set({ stagedChanges: [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : String(err) })
    }
  },

  applyChanges: async () => {
    set({ isLoading: true, error: null })
    try {
      const { stagedChanges } = get()
      const results = await window.api.applyChanges(stagedChanges)

      const failures = results.filter((r) => !r.success)
      if (failures.length > 0) {
        const errorMessages = failures
          .map((f) => f.error ?? `Change ${f.id} failed`)
          .join('; ')
        set({ error: `Some changes failed: ${errorMessages}` })
      }

      const stagedAfter = await window.api.getStagedChanges()
      set({ stagedChanges: stagedAfter })

      await get().rescan()
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
        isLoading: false,
      })
    }
  },

  setActiveSection: (section: ActiveSection) => {
    set({ activeSection: section })
  },

  toggleNonArcanum: () => {
    set((state) => ({ showNonArcanum: !state.showNonArcanum }))
  },

  toggleDarkMode: () => {
    set((state) => {
      const newDark = !state.darkMode
      applyDarkModeClass(newDark)
      return { darkMode: newDark }
    })
  },

  setError: (error: string) => {
    set({ error })
  },

  clearError: () => {
    set({ error: null })
  },

  addToast: (message: string, type: ToastType) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    set((state) => ({ toasts: [...state.toasts, { id, message, type }] }))
  },

  removeToast: (id: string) => {
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }))
  },

  setSearchQuery: (query: string) => {
    set({ searchQuery: query })
  },

  setSortMode: (mode: 'recent' | 'name') => {
    localStorage.setItem('sortMode', mode)
    set({ sortMode: mode })
  },
}))
