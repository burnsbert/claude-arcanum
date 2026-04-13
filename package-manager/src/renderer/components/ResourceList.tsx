import type {
  Agent,
  Command,
  Skill,
  InstalledResource,
  PendingChange,
  InstallStatus,
} from '../../shared/types'
import { ResourceCard } from './ResourceCard'
import { buildSourcePath } from '../store/appStore'

type StalenessMap = Record<string, 'current' | 'stale' | 'source-missing'>

interface ResourceListProps {
  section: 'agents' | 'commands' | 'skills'
  availableResources: (Agent | Command | Skill)[]
  installedResources: InstalledResource[]
  stagedChanges: PendingChange[]
  showNonArcanum: boolean
  defaultInstallMethod: 'symlink' | 'copy'
  repoPath: string
  targetDir: string
  stalenessMap: StalenessMap
  onStageInstall: (change: Omit<PendingChange, 'id'>) => void
  onStageRemove: (change: Omit<PendingChange, 'id'>) => void
  onStageUpdate: (change: Omit<PendingChange, 'id'>) => void
  onUnstage: (id: string) => void
  workflowMembership: Record<string, string[]>
}

function buildTargetPath(targetDir: string, type: 'agent' | 'command' | 'skill', name: string): string {
  const folder = type === 'agent' ? 'agents' : type === 'command' ? 'commands' : 'skills'
  if (type === 'skill') {
    return `${targetDir}/${folder}/${name}`
  }
  return `${targetDir}/${folder}/${name}.md`
}

function resourceTypeFromSection(section: 'agents' | 'commands' | 'skills'): 'agent' | 'command' | 'skill' {
  return section === 'agents' ? 'agent' : section === 'commands' ? 'command' : 'skill'
}

export function ResourceList({
  section,
  availableResources,
  installedResources,
  stagedChanges,
  showNonArcanum,
  defaultInstallMethod,
  repoPath,
  targetDir,
  stalenessMap,
  onStageInstall,
  onStageRemove,
  onStageUpdate,
  onUnstage,
  workflowMembership,
}: ResourceListProps) {
  const type = resourceTypeFromSection(section)

  /** Is this resource installed? Any source counts — symlink, copy, or manual placement. */
  function determineStatus(resource: Agent | Command | Skill): InstallStatus {
    const installed = installedResources.find(
      (r) => r.name === resource.name && r.type === type
    )

    if (!installed) return 'not-installed'

    if (installed.installType === 'copy') {
      const key = `${installed.name}:${installed.type}`
      const staleness = stalenessMap[key]
      if (staleness === 'stale') return 'update-available'
      return 'installed-copy'
    }

    if (installed.source === 'broken-symlink') return 'not-installed'

    return installed.installType === 'symlink' ? 'installed-symlink' : 'installed-copy'
  }

  /** Is something physically present at the target path (from any source)? */
  function targetOccupied(resource: Agent | Command | Skill): boolean {
    return installedResources.some(
      (r) => r.name === resource.name && r.type === type
    )
  }

  function findPending(resource: Agent | Command | Skill): PendingChange | undefined {
    const target = buildTargetPath(targetDir, type, resource.name)
    return stagedChanges.find((c) => c.targetPath === target)
  }

  function getWorkflowNames(resource: Agent | Command | Skill): string[] {
    const folder = type === 'agent' ? 'agents' : type === 'command' ? 'commands' : 'skills'
    const key = type === 'skill'
      ? `${folder}/${resource.name}`
      : `${folder}/${resource.name}.md`
    return workflowMembership[key] ?? []
  }

  function handleToggle(resource: Agent | Command | Skill) {
    const pending = findPending(resource)
    if (pending) {
      onUnstage(pending.id)
      return
    }

    const status = determineStatus(resource)
    const source = buildSourcePath(repoPath, type, resource)
    const target = buildTargetPath(targetDir, type, resource.name)
    const changeBase = {
      resourceType: type,
      resourceName: resource.name,
      sourcePath: source,
      targetPath: target,
      installMethod: defaultInstallMethod,
    } as const

    if (status === 'installed-symlink' || status === 'installed-copy') {
      // Installed from arcanum → uninstall
      onStageRemove({ ...changeBase, action: 'remove' })
    } else if (status === 'update-available') {
      // Stale arcanum copy → update
      onStageUpdate({ ...changeBase, action: 'update' })
    } else if (targetOccupied(resource)) {
      // Not from arcanum but something is at the target → replace
      onStageUpdate({ ...changeBase, action: 'update' })
    } else {
      // Nothing installed → fresh install
      onStageInstall({ ...changeBase, action: 'install' })
    }
  }

  function handleUpdate(resource: Agent | Command | Skill) {
    const source = buildSourcePath(repoPath, type, resource)
    const target = buildTargetPath(targetDir, type, resource.name)
    onStageUpdate({
      action: 'update',
      resourceType: type,
      resourceName: resource.name,
      sourcePath: source,
      targetPath: target,
      installMethod: defaultInstallMethod,
    })
  }

  // Non-arcanum resources (installed from other sources)
  const nonArcanumResources = showNonArcanum
    ? installedResources.filter(
        (r) => r.type === type && r.source !== 'arcanum' && r.source !== 'local'
      )
    : []

  if (availableResources.length === 0 && nonArcanumResources.length === 0) {
    const emoji = section === 'skills' ? '📦' : section === 'commands' ? '⌨️' : '🤖'
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-400 dark:text-gray-500">
        <span className="text-4xl mb-3">{emoji}</span>
        <p className="text-sm">No {section} available</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {availableResources.map((resource) => (
        <ResourceCard
          key={resource.name}
          resource={resource}
          type={type}
          status={determineStatus(resource)}
          pendingChange={findPending(resource)}
          workflowNames={getWorkflowNames(resource)}
          onToggle={() => handleToggle(resource)}
          onUpdate={determineStatus(resource) === 'update-available' ? () => handleUpdate(resource) : undefined}
        />
      ))}

      {nonArcanumResources.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
            Non-Arcanum Resources
          </h3>
          <div className="space-y-2 opacity-60">
            {nonArcanumResources.map((r) => (
              <div
                key={`${r.name}-${r.type}`}
                className="flex items-center justify-between px-4 py-2 rounded border border-gray-200 dark:border-gray-700 text-sm"
              >
                <span>{r.name}</span>
                <span className="text-xs text-gray-400">{r.source}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
