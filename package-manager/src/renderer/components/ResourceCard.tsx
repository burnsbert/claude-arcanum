import type { Agent, Command, Skill, PendingChange, InstallStatus } from '../../shared/types'
import { StatusBadge } from './StatusBadge'

interface ResourceCardProps {
  resource: Agent | Command | Skill
  type: 'agent' | 'command' | 'skill'
  status: InstallStatus
  pendingChange?: PendingChange
  workflowNames?: string[]
  onToggle: () => void
  onUpdate?: () => void
}

export function ResourceCard({
  resource,
  type,
  status,
  pendingChange,
  workflowNames,
  onToggle,
  onUpdate,
}: ResourceCardProps) {
  const isInstalled = status === 'installed-symlink' || status === 'installed-copy'
  const isPending = !!pendingChange

  // Pending: install/update → checked (will be installed), remove → unchecked
  const checked = isPending ? pendingChange.action !== 'remove' : isInstalled

  const typeBadgeColors = {
    agent: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    command: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    skill: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  }

  return (
    <div
      className={`border rounded-lg p-4 transition-all ${
        isPending
          ? 'border-amber-300 dark:border-amber-600 ring-1 ring-amber-200 dark:ring-amber-700'
          : 'border-gray-200 dark:border-gray-700'
      } bg-white dark:bg-gray-800`}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={checked}
          onChange={onToggle}
          className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm truncate">{resource.name}</span>
            <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium ${typeBadgeColors[type]}`}>
              {type}
            </span>
            {workflowNames && workflowNames.length > 0 && (
              workflowNames.length <= 2
                ? workflowNames.map((wf) => (
                    <span key={wf} className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                      WF: {wf}
                    </span>
                  ))
                : <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                    {workflowNames.length} workflows
                  </span>
            )}
          </div>

          {resource.description && (
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
              {resource.description}
            </p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusBadge status={status} pendingChange={pendingChange} />
          {status === 'update-available' && onUpdate && !isPending && (
            <button
              type="button"
              onClick={onUpdate}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Update
            </button>
          )}
        </div>
        {resource.lastUpdated && (
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            {new Date(resource.lastUpdated).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  )
}
