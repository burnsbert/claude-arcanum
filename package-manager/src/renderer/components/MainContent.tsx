import { useMemo } from 'react'
import { useAppStore } from '../store/appStore'
import type { Agent, Command, Skill, Workflow } from '../../shared/types'
import { WorkflowList } from './WorkflowList'
import { ResourceList } from './ResourceList'
import { ReviewChangesPanel } from './ReviewChangesPanel'
import { SettingsPage } from './SettingsPage'
import { FilterBar } from './FilterBar'

function LoadingSpinner() {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col items-center justify-center h-full py-24">
      <svg className="animate-spin h-10 w-10 text-indigo-500" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">Loading...</p>
    </div>
  )
}

function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center h-full py-24 text-center px-8">
      <p className="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">Something went wrong</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-6 max-w-sm">{error}</p>
      <button
        type="button"
        onClick={onRetry}
        className="px-4 py-2 rounded-md text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
      >
        Retry
      </button>
    </div>
  )
}

/**
 * Normalize a workflow member path to a canonical key.
 */
function normalizeMemberPath(p: string): string {
  return p.replace(/^\/+/, '').replace(/\/SKILL\.md$/i, '')
}

/**
 * Build canonical path key for a resource to match against workflow membership.
 */
function resourcePathKey(type: 'agent' | 'command' | 'skill', name: string): string {
  const folder = type === 'agent' ? 'agents' : type === 'command' ? 'commands' : 'skills'
  if (type === 'skill') {
    return `${folder}/${name}`
  }
  return `${folder}/${name}.md`
}

export function MainContent() {
  const {
    activeSection,
    plugin,
    installedResources,
    workflows,
    stagedChanges,
    showNonArcanum,
    config,
    sortMode,
    isLoading,
    error,
    stalenessMap,
    searchQuery,
    rescan,
    stageChange,
    unstageChange,
  } = useAppStore()

  const defaultInstallMethod = config?.defaultInstallMethod ?? 'symlink'
  const repoPath = config?.repoPath ?? ''
  const targetDir = '~/.claude'

  // Build workflow membership map: path key → workflow names
  const workflowMembership = useMemo((): Record<string, string[]> => {
    const map: Record<string, string[]> = {}
    for (const workflow of workflows) {
      for (const member of workflow.members) {
        const key = normalizeMemberPath(member.path)
        if (!map[key]) map[key] = []
        map[key].push(workflow.name)
      }
    }
    return map
  }, [workflows])

  const normalizedQuery = searchQuery.toLowerCase()

  function matchesSearch(resource: { name: string; description?: string }): boolean {
    if (!normalizedQuery) return true
    return (
      resource.name.toLowerCase().includes(normalizedQuery) ||
      (resource.description?.toLowerCase().includes(normalizedQuery) ?? false)
    )
  }

  function sortResources<T extends { name: string; lastUpdated?: string }>(items: T[]): T[] {
    return [...items].sort((a, b) => {
      if (sortMode === 'name') return a.name.localeCompare(b.name)
      const ta = a.lastUpdated ? new Date(a.lastUpdated).getTime() : 0
      const tb = b.lastUpdated ? new Date(b.lastUpdated).getTime() : 0
      return tb - ta
    })
  }

  const availableAgents = useMemo((): Agent[] => {
    return sortResources((plugin?.agents ?? []).filter(matchesSearch))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plugin, normalizedQuery, sortMode])

  const availableCommands = useMemo((): Command[] => {
    return sortResources((plugin?.commands ?? []).filter(matchesSearch))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plugin, normalizedQuery, sortMode])

  const availableSkills = useMemo((): Skill[] => {
    return sortResources((plugin?.skills ?? []).filter(matchesSearch))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plugin, normalizedQuery, sortMode])

  const filteredWorkflows = useMemo((): Workflow[] => {
    const filtered = workflows.filter((w) => {
      if (!normalizedQuery) return true
      return (
        w.name.toLowerCase().includes(normalizedQuery) ||
        w.description?.toLowerCase().includes(normalizedQuery) ||
        w.members.some((m) => m.name.toLowerCase().includes(normalizedQuery))
      )
    })
    return sortResources(filtered)
  }, [workflows, normalizedQuery, sortMode])

  const batchUnstage = useAppStore((s) => s.batchUnstage)

  if (isLoading && activeSection !== 'review') {
    return <LoadingSpinner />
  }

  if (error) {
    return <ErrorState error={error} onRetry={rescan} />
  }

  if (activeSection === 'settings') {
    return (
      <div className="p-6">
        <SettingsPage />
      </div>
    )
  }

  if (activeSection === 'review') {
    return <ReviewChangesPanel />
  }

  if (activeSection === 'workflows') {
    return (
      <div className="flex flex-col h-full">
        <FilterBar />
        <div className="p-6 flex-1 overflow-auto">
          <WorkflowList
            workflows={filteredWorkflows}
            installedResources={installedResources}
            stagedChanges={stagedChanges}
            defaultInstallMethod={defaultInstallMethod}
            repoPath={repoPath}
            targetDir={targetDir}
            onStageInstall={stageChange}
            onStageRemove={stageChange}
            onBatchUnstage={batchUnstage}
          />
        </div>
      </div>
    )
  }

  if (activeSection === 'skills') {
    return (
      <div className="flex flex-col h-full">
        <FilterBar />
        <div className="p-6 flex-1 overflow-auto">
          <ResourceList
            section="skills"
            availableResources={availableSkills}
            installedResources={installedResources}
            stagedChanges={stagedChanges}
            showNonArcanum={showNonArcanum}
            defaultInstallMethod={defaultInstallMethod}
            repoPath={repoPath}
            targetDir={targetDir}
            stalenessMap={stalenessMap}
            onStageInstall={stageChange}
            onStageRemove={stageChange}
            onStageUpdate={stageChange}
            onUnstage={unstageChange}
            workflowMembership={workflowMembership}
          />
        </div>
      </div>
    )
  }

  if (activeSection === 'commands') {
    return (
      <div className="flex flex-col h-full">
        <FilterBar />
        <div className="p-6 flex-1 overflow-auto">
          <ResourceList
            section="commands"
            availableResources={availableCommands}
            installedResources={installedResources}
            stagedChanges={stagedChanges}
            showNonArcanum={showNonArcanum}
            defaultInstallMethod={defaultInstallMethod}
            repoPath={repoPath}
            targetDir={targetDir}
            stalenessMap={stalenessMap}
            onStageInstall={stageChange}
            onStageRemove={stageChange}
            onStageUpdate={stageChange}
            onUnstage={unstageChange}
            workflowMembership={workflowMembership}
          />
        </div>
      </div>
    )
  }

  if (activeSection === 'agents') {
    return (
      <div className="flex flex-col h-full">
        <FilterBar />
        <div className="p-6 flex-1 overflow-auto">
          <ResourceList
            section="agents"
            availableResources={availableAgents}
            installedResources={installedResources}
            stagedChanges={stagedChanges}
            showNonArcanum={showNonArcanum}
            defaultInstallMethod={defaultInstallMethod}
            repoPath={repoPath}
            targetDir={targetDir}
            stalenessMap={stalenessMap}
            onStageInstall={stageChange}
            onStageRemove={stageChange}
            onStageUpdate={stageChange}
            onUnstage={unstageChange}
            workflowMembership={workflowMembership}
          />
        </div>
      </div>
    )
  }

  return null
}
