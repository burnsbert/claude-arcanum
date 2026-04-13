import { readdir, readFile, stat } from 'fs/promises'
import { join, basename } from 'path'
import type { Plugin, Agent, Command, Skill } from '@shared/types'
import { parseFrontMatter } from './yaml-parser'

/**
 * Scans the arcanum repo root for resources and returns a single Plugin object.
 *
 * Reads plugin metadata from .claude-plugin/plugin.json.
 * Scans agents/*.md (excludes personalities/ subdirectory).
 * Scans commands/*.md.
 * Scans skills/SKILL.md directories.
 */
export async function scanRepo(repoRoot: string): Promise<Plugin> {
  const { name, version, description } = await loadPluginMeta(repoRoot)

  const [agents, commands, skills] = await Promise.all([
    loadAgents(repoRoot),
    loadCommands(repoRoot),
    loadSkills(repoRoot)
  ])

  return { id: 'arcanum', name, version, description, agents, commands, skills }
}

interface PluginMeta {
  name: string
  version: string
  description: string
}

async function loadPluginMeta(repoRoot: string): Promise<PluginMeta> {
  const metaPath = join(repoRoot, '.claude-plugin', 'plugin.json')
  try {
    const raw = await readFile(metaPath, 'utf-8')
    const parsed = JSON.parse(raw) as Record<string, unknown>
    return {
      name: typeof parsed.name === 'string' ? parsed.name : 'arcanum',
      version: typeof parsed.version === 'string' ? parsed.version : '',
      description: typeof parsed.description === 'string' ? parsed.description : ''
    }
  } catch {
    return { name: 'arcanum', version: '', description: '' }
  }
}

async function loadAgents(repoRoot: string): Promise<Agent[]> {
  const agentsDir = join(repoRoot, 'agents')

  let files: string[]
  try {
    const entries = await readdir(agentsDir, { withFileTypes: true })
    // Only top-level .md files — exclude subdirectories like personalities/
    files = entries.filter(e => e.isFile() && e.name.endsWith('.md')).map(e => e.name)
  } catch {
    return []
  }

  const agents = await Promise.all(
    files.map(async filename => {
      const filePath = join(agentsDir, filename)
      const fileNameBase = basename(filename, '.md')

      let data: Record<string, unknown> = {}
      let lastUpdated: string | undefined
      try {
        const [content, fileStat] = await Promise.all([
          readFile(filePath, 'utf-8'),
          stat(filePath)
        ])
        data = parseFrontMatter(content).data
        lastUpdated = fileStat.mtime.toISOString()
      } catch {
        // Unreadable file — use defaults
      }

      const agent: Agent = {
        name: typeof data.name === 'string' && data.name ? data.name : fileNameBase,
        description: typeof data.description === 'string' ? data.description : ''
      }

      if (typeof data.model === 'string') agent.model = data.model
      if (Array.isArray(data.tools)) agent.tools = data.tools as string[]
      if (typeof data.color === 'string') agent.color = data.color
      if (lastUpdated !== undefined) agent.lastUpdated = lastUpdated

      return agent
    })
  )

  return agents
}

async function loadCommands(repoRoot: string): Promise<Command[]> {
  const commandsDir = join(repoRoot, 'commands')

  let files: string[]
  try {
    const entries = await readdir(commandsDir, { withFileTypes: true })
    files = entries.filter(e => e.isFile() && e.name.endsWith('.md')).map(e => e.name)
  } catch {
    return []
  }

  const commands = await Promise.all(
    files.map(async filename => {
      const filePath = join(commandsDir, filename)
      const fileNameBase = basename(filename, '.md')

      let data: Record<string, unknown> = {}
      let lastUpdated: string | undefined
      try {
        const [content, fileStat] = await Promise.all([
          readFile(filePath, 'utf-8'),
          stat(filePath)
        ])
        data = parseFrontMatter(content).data
        lastUpdated = fileStat.mtime.toISOString()
      } catch {
        // Unreadable file — use defaults
      }

      // Commands use filename as name; name field in front matter is ignored
      const command: Command = {
        name: fileNameBase,
        description: typeof data.description === 'string' ? data.description : ''
      }

      if (Array.isArray(data['allowed-tools'])) {
        command.allowedTools = data['allowed-tools'] as string[]
      }
      if (typeof data['argument-hint'] === 'string') {
        command.argumentHint = data['argument-hint']
      }
      if (lastUpdated !== undefined) command.lastUpdated = lastUpdated

      return command
    })
  )

  return commands
}

async function loadSkills(repoRoot: string): Promise<Skill[]> {
  const skillsDir = join(repoRoot, 'skills')

  let skillDirNames: string[]
  try {
    const entries = await readdir(skillsDir, { withFileTypes: true })
    skillDirNames = entries.filter(e => e.isDirectory()).map(e => e.name)
  } catch {
    return []
  }

  const skills: Skill[] = []

  for (const dirName of skillDirNames) {
    const skillDir = join(skillsDir, dirName)
    const skillMdPath = join(skillDir, 'SKILL.md')

    let data: Record<string, unknown> = {}
    let hasSkillMd = false
    let lastUpdated: string | undefined

    try {
      const [content, fileStat] = await Promise.all([
        readFile(skillMdPath, 'utf-8'),
        stat(skillMdPath)
      ])
      data = parseFrontMatter(content).data
      hasSkillMd = true
      lastUpdated = fileStat.mtime.toISOString()
    } catch {
      // No SKILL.md or unreadable — skip
    }

    if (!hasSkillMd) continue

    const skill: Skill = {
      name: typeof data.name === 'string' && data.name ? data.name : dirName,
      description: typeof data.description === 'string' ? data.description : '',
      dirPath: skillDir
    }

    if (Array.isArray(data['allowed-tools'])) {
      skill.allowedTools = data['allowed-tools'] as string[]
    }
    if (typeof data['user-invocable'] === 'boolean') {
      skill.userInvocable = data['user-invocable']
    }
    if (typeof data['argument-hint'] === 'string') {
      skill.argumentHint = data['argument-hint']
    }
    if (lastUpdated !== undefined) skill.lastUpdated = lastUpdated

    skills.push(skill)
  }

  return skills
}
