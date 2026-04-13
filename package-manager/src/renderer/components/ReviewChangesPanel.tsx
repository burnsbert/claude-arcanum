import { useState, useRef } from 'react'
import { useAppStore } from '../store/appStore'
import type { PendingChange, ApplyResult } from '../../shared/types'

type PanelState = 'idle' | 'applying' | 'done' | 'partial-failure'

export function ReviewChangesPanel() {
  const {
    stagedChanges,
    unstageChange,
    applyChanges,
    setActiveSection,
    addToast,
  } = useAppStore()

  const [state, setState] = useState<PanelState>('idle')
  const [results, setResults] = useState<ApplyResult[]>([])
  // Snapshot changes before apply clears them
  const appliedChangesRef = useRef<PendingChange[]>([])

  const installs = stagedChanges.filter((c) => c.action === 'install')
  const removes = stagedChanges.filter((c) => c.action === 'remove')
  const updates = stagedChanges.filter((c) => c.action === 'update')

  const handleApply = async () => {
    appliedChangesRef.current = [...stagedChanges]
    setState('applying')
    try {
      await applyChanges()
      const stagedAfter = useAppStore.getState().stagedChanges
      if (stagedAfter.length === 0) {
        setState('done')
      } else {
        setState('partial-failure')
        addToast('Some changes failed', 'error')
      }
    } catch {
      setState('partial-failure')
      addToast('Apply failed', 'error')
    }
  }

  function ChangeRow({ change, applied }: { change: PendingChange; applied?: boolean }) {
    const failed = results.find((r) => r.id === change.id && !r.success)
    return (
      <div className={`flex items-center gap-3 px-4 py-2.5 rounded-md text-sm ${
        failed ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50 dark:bg-gray-700/50'
      }`}>
        <span className="font-medium flex-1 truncate">{change.resourceName}</span>
        <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-gray-300">
          {change.resourceType}
        </span>
        <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-gray-300">
          {change.installMethod}
        </span>
        {failed && (
          <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
            Failed
          </span>
        )}
        {state === 'idle' && !applied && (
          <button
            type="button"
            onClick={() => unstageChange(change.id)}
            className="text-gray-400 hover:text-red-500 transition-colors"
            aria-label={`Remove ${change.resourceName}`}
          >
            ✕
          </button>
        )}
      </div>
    )
  }

  function ChangeGroup({ title, changes, applied }: { title: string; changes: PendingChange[]; applied?: boolean }) {
    if (changes.length === 0) return null
    return (
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
          {title} ({changes.length})
        </h3>
        <div className="space-y-1.5">
          {changes.map((c) => (
            <ChangeRow key={c.id} change={c} applied={applied} />
          ))}
        </div>
      </div>
    )
  }

  // For the done state, show what was applied
  const applied = appliedChangesRef.current
  const appliedInstalls = applied.filter((c) => c.action === 'install')
  const appliedRemoves = applied.filter((c) => c.action === 'remove')
  const appliedUpdates = applied.filter((c) => c.action === 'update')

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-6">
        <h2 className="text-lg font-bold mb-6">Review Changes</h2>

        {state === 'done' ? (
          <>
            <div className="mb-6 px-4 py-3 rounded-md bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 text-sm font-medium">
              All changes applied successfully
            </div>
            <ChangeGroup title="Installed" changes={appliedInstalls} applied />
            <ChangeGroup title="Removed" changes={appliedRemoves} applied />
            <ChangeGroup title="Updated" changes={appliedUpdates} applied />
          </>
        ) : state === 'applying' ? (
          <div className="flex flex-col items-center justify-center py-16">
            <svg
              className="animate-spin h-8 w-8 text-indigo-500 mb-3"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-gray-500">Applying changes...</p>
          </div>
        ) : stagedChanges.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400 dark:text-gray-500">
            <p className="text-sm">No changes staged</p>
          </div>
        ) : (
          <>
            <ChangeGroup title="Installing" changes={installs} />
            <ChangeGroup title="Removing" changes={removes} />
            <ChangeGroup title="Updating" changes={updates} />
          </>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-3">
        <button
          type="button"
          onClick={() => setActiveSection('workflows')}
          className="px-4 py-2 text-sm rounded-md bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
        >
          {state === 'done' ? 'Done' : 'Close'}
        </button>
        {state === 'idle' && stagedChanges.length > 0 && (
          <button
            type="button"
            onClick={handleApply}
            className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
          >
            Confirm Changes
          </button>
        )}
      </div>
    </div>
  )
}
