import type {
  Workflow,
  InstalledResource,
  PendingChange,
} from '../../shared/types'
import { WorkflowCard } from './WorkflowCard'

interface WorkflowListProps {
  workflows: Workflow[]
  installedResources: InstalledResource[]
  stagedChanges: PendingChange[]
  defaultInstallMethod: 'symlink' | 'copy'
  repoPath: string
  targetDir: string
  onStageInstall: (change: Omit<PendingChange, 'id'>) => void
  onStageRemove: (change: Omit<PendingChange, 'id'>) => void
  onBatchUnstage: (ids: string[]) => void
}

export function WorkflowList({
  workflows,
  installedResources,
  stagedChanges,
  defaultInstallMethod,
  repoPath,
  targetDir,
  onStageInstall,
  onStageRemove,
  onBatchUnstage,
}: WorkflowListProps) {
  if (workflows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-400 dark:text-gray-500">
        <span className="text-4xl mb-3">🔄</span>
        <p className="text-sm">No workflows defined</p>
        <p className="text-xs mt-1">Add a workflows.json to define workflow groupings</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {workflows.map((workflow) => (
        <WorkflowCard
          key={workflow.id}
          workflow={workflow}
          allWorkflows={workflows}
          installedResources={installedResources}
          stagedChanges={stagedChanges}
          defaultInstallMethod={defaultInstallMethod}
          repoPath={repoPath}
          targetDir={targetDir}
          onStageInstall={onStageInstall}
          onStageRemove={onStageRemove}
          onBatchUnstage={onBatchUnstage}
        />
      ))}
    </div>
  )
}
