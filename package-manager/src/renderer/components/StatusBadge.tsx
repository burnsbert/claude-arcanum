import type { InstallStatus, PendingChange } from '../../shared/types'

interface StatusBadgeProps {
  status: InstallStatus
  pendingChange?: PendingChange
}

export function StatusBadge({ status, pendingChange }: StatusBadgeProps) {
  // Pending changes override the base status
  if (pendingChange) {
    const label = pendingChange.action === 'install'
      ? 'To Install'
      : pendingChange.action === 'remove'
      ? 'To Uninstall'
      : 'To Update'
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
        {label}
      </span>
    )
  }

  const configs: Record<InstallStatus, { label: string; classes: string }> = {
    'installed-symlink': {
      label: 'Symlink',
      classes: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    },
    'installed-copy': {
      label: 'Copy',
      classes: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    },
    'update-available': {
      label: 'Update Available',
      classes: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    },
    'not-installed': {
      label: 'Not Installed',
      classes: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
    },
    'orphaned': {
      label: 'Orphaned',
      classes: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    }
  }

  const { label, classes } = configs[status]

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${classes}`}>
      {label}
    </span>
  )
}
