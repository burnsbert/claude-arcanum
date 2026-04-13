import { useState, useRef, useEffect } from 'react'
import type { Workflow, WorkflowMember, InstalledResource, PendingChange } from '../../shared/types'
import { StatusBadge } from './StatusBadge'

export interface WorkflowCardProps {
  workflow: Workflow
  allWorkflows: Workflow[]
  installedResources: InstalledResource[]
  stagedChanges: PendingChange[]
  defaultInstallMethod: 'symlink' | 'copy'
  repoPath: string
  targetDir: string
  onStageInstall: (change: Omit<PendingChange, 'id'>) => void
  onStageRemove: (change: Omit<PendingChange, 'id'>) => void
  onBatchUnstage: (ids: string[]) => void
}

/** Aggregated install status for the whole workflow */
type WorkflowStatus = 'all-installed' | 'not-installed'

/** Type badge for workflow member resource type */
function MemberTypeBadge({ type }: { type: 'agent' | 'command' | 'skill' }) {
  const config = {
    agent: { label: 'Agent', className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' },
    command: { label: 'Command', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' },
    skill: { label: 'Skill', className: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300' },
  }
  const { label, className } = config[type]
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}>
      {label}
    </span>
  )
}

/**
 * Normalize a path for comparison: strip leading slashes and strip a trailing
 * "/SKILL.md" so that skill directory paths and SKILL.md paths compare equal.
 */
function normalizeMemberPath(p: string): string {
  return p.replace(/^\/+/, '').replace(/\/SKILL\.md$/i, '')
}

/** Find the matching installed resource for a workflow member, if any. */
function findInstalledMember(member: WorkflowMember, installedResources: InstalledResource[]): InstalledResource | undefined {
  const normalizedMember = normalizeMemberPath(member.path)
  return installedResources.find((r) => {
    if (r.repoPath) {
      const normalizedInstalled = normalizeMemberPath(r.repoPath)
      if (normalizedInstalled === normalizedMember) return true
    }
    return r.name === member.name && r.type === member.type
  })
}

/** Check whether a workflow member is installed by matching its path against installedResources. */
function isMemberInstalled(member: WorkflowMember, installedResources: InstalledResource[]): boolean {
  return findInstalledMember(member, installedResources) !== undefined
}

/** Compute aggregated install status for a workflow */
function computeWorkflowStatus(
  workflow: Workflow,
  installedResources: InstalledResource[]
): WorkflowStatus {
  if (workflow.members.length === 0) return 'not-installed'
  return workflow.members.every((m) => isMemberInstalled(m, installedResources))
    ? 'all-installed'
    : 'not-installed'
}

/**
 * Returns the subset of members that should be removed when uninstalling this
 * workflow. Members whose paths are also owned by another fully-installed
 * workflow are retained — they will stay on disk.
 */
function computeMembersToRemove(
  workflow: Workflow,
  allWorkflows: Workflow[],
  installedResources: InstalledResource[]
): WorkflowMember[] {
  const retainedPaths = new Set<string>()
  for (const other of allWorkflows) {
    if (other.id === workflow.id) continue
    if (computeWorkflowStatus(other, installedResources) !== 'all-installed') continue
    for (const m of other.members) {
      retainedPaths.add(normalizeMemberPath(m.path))
    }
  }
  return workflow.members.filter((m) => !retainedPaths.has(normalizeMemberPath(m.path)))
}

/** Build the target path for a workflow member resource */
function buildTargetPath(member: WorkflowMember, targetDir: string): string {
  const folder = member.type === 'agent' ? 'agents' : member.type === 'command' ? 'commands' : 'skills'
  const baseName = member.path.split('/').pop() ?? member.name
  // Skills are directories (no .md extension), agents and commands are .md files
  const ext = member.type === 'skill' ? '' : baseName.endsWith('.md') ? '' : '.md'
  return `${targetDir}/${folder}/${baseName}${ext}`
}

/** Build the source path for a workflow member resource */
function buildSourcePath(member: WorkflowMember, repoPath: string): string {
  return `${repoPath}/${member.path.replace(/^\/+/, '')}`
}

/** Compute the aggregate install method label for installed workflow members */
function computeInstallMethodLabel(
  workflow: Workflow,
  installedResources: InstalledResource[]
): 'symlink' | 'copy' | 'mixed' | null {
  const types = new Set<string>()
  for (const member of workflow.members) {
    const installed = findInstalledMember(member, installedResources)
    if (installed) {
      types.add(installed.installType === 'unknown' ? 'copy' : installed.installType)
    }
  }
  if (types.size === 0) return null
  if (types.size === 1) return types.values().next().value as 'symlink' | 'copy'
  return 'mixed'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

/** Aggregate status badge shown in the card header.
 *  Shows pending action labels when the effective state differs from installed state. */
function WorkflowStatusBadge({ installedStatus, effectiveStatus, isPending, installMethod }: {
  installedStatus: WorkflowStatus
  effectiveStatus: WorkflowStatus
  isPending: boolean
  installMethod: 'symlink' | 'copy' | 'mixed' | null
}) {
  if (isPending) {
    if (installedStatus === 'all-installed' && effectiveStatus === 'not-installed') {
      return (
        <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
          To Uninstall
        </span>
      )
    }
    if (installedStatus === 'not-installed' && effectiveStatus === 'all-installed') {
      return (
        <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
          To Install
        </span>
      )
    }
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
        Pending Changes
      </span>
    )
  }

  if (effectiveStatus === 'all-installed') {
    const methodLabel = installMethod === 'mixed' ? 'mixed' : installMethod ?? 'symlink'
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        Installed ({methodLabel})
      </span>
    )
  }
  return (
    <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
      Not Installed
    </span>
  )
}

/** A single expanded member row (read-only) */
function MemberRow({
  member,
  installed,
}: {
  member: WorkflowMember
  installed: InstalledResource | undefined
}) {
  const showDescription = member.type !== 'agent' && member.description

  let status: 'installed-symlink' | 'installed-copy' | 'not-installed' = 'not-installed'
  if (installed) {
    status = installed.installType === 'copy' ? 'installed-copy' : 'installed-symlink'
  }

  return (
    <div className="flex items-start gap-2 py-2 px-3 rounded-md bg-gray-50 dark:bg-gray-700/50">
      <MemberTypeBadge type={member.type} />
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium text-gray-800 dark:text-gray-200 block truncate">
          {member.name}
        </span>
        {showDescription && (
          <span className="text-sm text-gray-500 dark:text-gray-400 block mt-0.5 leading-relaxed">
            {member.description}
          </span>
        )}
      </div>
      <StatusBadge status={status} />
    </div>
  )
}

/** Checkbox with indeterminate support for workflow aggregate state */
function WorkflowCheckbox({
  checked,
  indeterminate,
  isPending,
  onChange,
  ariaLabel,
}: {
  checked: boolean
  indeterminate: boolean
  isPending: boolean
  onChange: () => void
  ariaLabel: string
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.indeterminate = indeterminate
    }
  }, [indeterminate])

  return (
    <label className="relative flex items-center cursor-pointer flex-shrink-0" aria-label={ariaLabel}>
      <input
        ref={inputRef}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="sr-only peer"
      />
      <span
        className={[
          'w-5 h-5 rounded border-2 flex items-center justify-center transition-all',
          isPending ? 'animate-pulse' : '',
          checked || indeterminate
            ? 'bg-indigo-500 border-indigo-500 text-white'
            : 'bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-500 hover:border-indigo-400 dark:hover:border-indigo-400',
          'peer-focus-visible:ring-2 peer-focus-visible:ring-indigo-500 peer-focus-visible:ring-offset-1',
        ].join(' ')}
        aria-hidden="true"
      >
        {checked && !indeterminate && (
          <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="2 6 5 9 10 3" />
          </svg>
        )}
        {indeterminate && (
          <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="2" y1="6" x2="10" y2="6" />
          </svg>
        )}
      </span>
    </label>
  )
}

/** WorkflowCard -- card with expand/collapse to show member resources.
 *
 *  Uses a div as the clickable header (not a button) so that the checkbox
 *  nested inside it remains a proper input without violating the HTML spec
 *  (interactive elements cannot be nested inside buttons). */
export function WorkflowCard({
  workflow,
  allWorkflows,
  installedResources,
  stagedChanges,
  defaultInstallMethod,
  repoPath,
  targetDir,
  onStageInstall,
  onStageRemove,
  onBatchUnstage,
}: WorkflowCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const installedStatus = computeWorkflowStatus(workflow, installedResources)

  const TYPE_ORDER = { skill: 0, command: 1, agent: 2 } as const
  const sortedMembers = [...workflow.members].sort(
    (a, b) => (TYPE_ORDER[a.type] ?? 3) - (TYPE_ORDER[b.type] ?? 3)
  )

  // Build a map of staged changes for this workflow's members
  const memberNames = new Set(workflow.members.map((m) => m.name))
  const stagedForWorkflow = stagedChanges.filter((c) => memberNames.has(c.resourceName))
  const isPending = stagedForWorkflow.length > 0

  // Compute EFFECTIVE state: what would be true after staged changes are applied
  const effectiveMemberStates = workflow.members.map((member) => {
    const isCurrentlyInstalled = isMemberInstalled(member, installedResources)
    const staged = stagedForWorkflow.find((c) => c.resourceName === member.name)
    if (staged) {
      if (staged.action === 'install') return true
      if (staged.action === 'remove') return false
    }
    return isCurrentlyInstalled
  })
  const effectiveAllInstalled = effectiveMemberStates.every(Boolean)

  function handleToggle() {
    setIsExpanded((v) => !v)
  }

  function handleCheckboxChange() {
    // If there are any pending changes for this workflow, clicking UNDOES them all
    // (returns to the original installed/uninstalled state)
    if (isPending) {
      onBatchUnstage(stagedForWorkflow.map((s) => s.id))
      return
    }

    // No pending changes — toggle based on current installed state
    if (installedStatus === 'all-installed') {
      // Stage remove only for members not shared with other installed workflows
      const membersToRemove = computeMembersToRemove(workflow, allWorkflows, installedResources)
      for (const member of membersToRemove) {
        onStageRemove({
          action: 'remove',
          resourceType: member.type,
          resourceName: member.name,
          sourcePath: buildSourcePath(member, repoPath),
          targetPath: buildTargetPath(member, targetDir),
          installMethod: defaultInstallMethod,
        })
      }
    } else {
      // Stage install for all missing members
      for (const member of workflow.members) {
        if (!isMemberInstalled(member, installedResources)) {
          onStageInstall({
            action: 'install',
            resourceType: member.type,
            resourceName: member.name,
            sourcePath: buildSourcePath(member, repoPath),
            targetPath: buildTargetPath(member, targetDir),
            installMethod: defaultInstallMethod,
          })
        }
      }
    }
  }

  return (
    <article
      aria-label={`Workflow: ${workflow.name}`}
      className={[
        'rounded-lg bg-gray-50 dark:bg-gray-800 transition-shadow shadow-sm hover:shadow-md',
        isPending
          ? 'border-2 border-amber-400 dark:border-amber-500'
          : 'border border-gray-200 dark:border-gray-700',
      ].join(' ')}
    >
      {/* Header area -- clickable to expand/collapse.
          Uses a div with role="button" and keyboard handler so we can embed
          the checkbox without violating nested-interactive rules. */}
      <div
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        aria-controls={`workflow-members-${workflow.id}`}
        onClick={handleToggle}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handleToggle()
          }
        }}
        className="flex items-start gap-3 px-4 py-4 cursor-pointer rounded-t-lg focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 select-none"
      >
        {/* Checkbox — stop propagation so clicking it doesn't toggle expand */}
        <div
          className="mt-0.5 flex-shrink-0"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
          role="none"
        >
          <WorkflowCheckbox
            checked={effectiveAllInstalled}
            indeterminate={false}
            isPending={isPending}
            onChange={handleCheckboxChange}
            ariaLabel={
              effectiveAllInstalled
                ? `Uninstall workflow: ${workflow.name}`
                : `Install workflow: ${workflow.name}`
            }
          />
        </div>

        {/* Name, description, status */}
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 leading-snug">
            {workflow.name}
          </h3>
          {workflow.description && (
            <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-2">
              {workflow.description}
            </p>
          )}
          <div className="mt-1.5 flex items-center gap-2">
            <WorkflowStatusBadge
              installedStatus={installedStatus}
              effectiveStatus={effectiveAllInstalled ? 'all-installed' : 'not-installed'}
              isPending={isPending}
              installMethod={computeInstallMethodLabel(workflow, installedResources)}
            />
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {workflow.members.length} component{workflow.members.length !== 1 ? 's' : ''}
            </span>
            {workflow.lastUpdated && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                · Updated: {formatDate(workflow.lastUpdated)}
              </span>
            )}
          </div>
        </div>

        {/* Right side: expand chevron */}
        <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
          <span
            aria-hidden="true"
            className={[
              'text-gray-400 dark:text-gray-500 transition-transform duration-200 text-sm',
              isExpanded ? 'rotate-180 inline-block' : 'inline-block',
            ].join(' ')}
          >
            ▾
          </span>
        </div>
      </div>

      {/* Expandable member list -- smooth max-height transition */}
      <div
        id={`workflow-members-${workflow.id}`}
        className={[
          'overflow-hidden transition-all duration-200 ease-in-out',
          isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0',
        ].join(' ')}
        aria-hidden={!isExpanded}
      >
        <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700 pt-3">
          {workflow.members.length > 0 ? (
            <>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
                Components
              </p>
              <div className="flex flex-col gap-1.5">
                {sortedMembers.map((member) => (
                  <MemberRow
                    key={`${member.type}-${member.name}`}
                    member={member}
                    installed={findInstalledMember(member, installedResources)}
                  />
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500">No components defined.</p>
          )}
        </div>
      </div>
    </article>
  )
}
