import { useEffect, useState } from 'react'
import { useAppStore } from '../store/appStore'
import type { RepoStatus } from '../../shared/types'

const NAV_ITEMS = [
  { id: 'workflows', label: 'Workflows' },
  { id: 'skills', label: 'Skills' },
  { id: 'commands', label: 'Commands' },
  { id: 'agents', label: 'Agents' },
] as const

export function Sidebar() {
  const {
    activeSection,
    setActiveSection,
    plugin,
    workflows,
    config,
    rescan,
    addToast,
    searchQuery,
  } = useAppStore()

  const [repoStatus, setRepoStatus] = useState<RepoStatus | null>(null)
  const [pulling, setPulling] = useState(false)

  // Check repo status on mount
  useEffect(() => {
    if (!config?.repoPath) return
    window.api.checkRepoStatus(config.repoPath).then(setRepoStatus).catch(() => {})
  }, [config?.repoPath])

  const handlePull = async () => {
    if (!config?.repoPath) return
    setPulling(true)
    try {
      const result = await window.api.gitPull(config.repoPath)
      if (result.success) {
        addToast('Pulled latest changes', 'success')
        await rescan()
        const newStatus = await window.api.checkRepoStatus(config.repoPath)
        setRepoStatus(newStatus)
      } else {
        addToast(`Pull failed: ${result.error}`, 'error')
      }
    } catch {
      addToast('Pull failed', 'error')
    } finally {
      setPulling(false)
    }
  }

  const normalizedQuery = searchQuery.toLowerCase()

  function getCount(section: string): number {
    if (!plugin) return 0
    let items: Array<{ name: string; description?: string }>
    switch (section) {
      case 'workflows':
        items = workflows
        break
      case 'skills':
        items = plugin.skills
        break
      case 'commands':
        items = plugin.commands
        break
      case 'agents':
        items = plugin.agents
        break
      default:
        return 0
    }
    if (!normalizedQuery) return items.length
    return items.filter(
      (r) =>
        r.name.toLowerCase().includes(normalizedQuery) ||
        (r.description?.toLowerCase().includes(normalizedQuery) ?? false)
    ).length
  }

  return (
    <aside className="w-60 shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = activeSection === item.id
          const count = getCount(item.id)
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveSection(item.id as typeof activeSection)}
              className={`w-full flex items-center justify-between px-6 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                  : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700/50'
              }`}
            >
              {item.label}
              <span className={`text-xs rounded-full px-2 py-0.5 ${
                isActive
                  ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-800 dark:text-indigo-200'
                  : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
              }`}>
                {count}
              </span>
            </button>
          )
        })}
      </nav>

      {/* Repo status */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-3 space-y-2">
        {repoStatus?.isGitRepo && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {repoStatus.updatesAvailable ? (
              <button
                type="button"
                onClick={handlePull}
                disabled={pulling}
                className="text-indigo-600 dark:text-indigo-400 hover:underline disabled:opacity-50"
              >
                {pulling ? 'Pulling...' : `${repoStatus.behindCount} update${repoStatus.behindCount === 1 ? '' : 's'} available`}
              </button>
            ) : (
              <span>Repo up to date</span>
            )}
          </div>
        )}
        {repoStatus && !repoStatus.isGitRepo && (
          <div className="text-xs text-amber-500">Not a git repo</div>
        )}
      </div>

      {/* Settings */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-3">
        <button
          type="button"
          onClick={() => setActiveSection('settings')}
          className={`w-full flex items-center justify-between text-sm ${
            activeSection === 'settings'
              ? 'text-indigo-700 dark:text-indigo-300'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          Settings
          {plugin?.version && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              v{plugin.version}
            </span>
          )}
        </button>
      </div>
    </aside>
  )
}
