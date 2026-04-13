import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs'
import { dirname, join, resolve } from 'path'
import type { AppConfig } from '@shared/types'

const DEFAULT_CONFIG: AppConfig = {
  repoPath: '',
  defaultInstallMethod: 'symlink',
  theme: 'system'
}

/**
 * Auto-detect the arcanum repo path by walking up from a starting directory
 * looking for .claude-plugin/plugin.json (the marker for this repo).
 */
export function detectRepoPath(startDir?: string): string | null {
  let dir = startDir ?? resolve(__dirname, '..', '..')

  for (let i = 0; i < 10; i++) {
    const pluginJson = join(dir, '.claude-plugin', 'plugin.json')
    if (existsSync(pluginJson)) {
      return dir
    }
    const parent = dirname(dir)
    if (parent === dir) break
    dir = parent
  }

  return null
}

/**
 * Manages application configuration with JSON file persistence.
 */
export class ConfigService {
  private configPath: string
  private config: AppConfig

  constructor(configPath: string) {
    this.configPath = configPath
    this.config = this.loadConfig()
  }

  private loadConfig(): AppConfig {
    try {
      const raw = readFileSync(this.configPath, 'utf-8')
      const parsed = JSON.parse(raw) as Partial<AppConfig>
      return { ...DEFAULT_CONFIG, ...parsed }
    } catch {
      return { ...DEFAULT_CONFIG }
    }
  }

  private saveConfig(): void {
    try {
      mkdirSync(dirname(this.configPath), { recursive: true })
      writeFileSync(this.configPath, JSON.stringify(this.config, null, 2))
    } catch {
      // Silently fail — config persistence is non-critical
    }
  }

  getConfig(): AppConfig {
    return { ...this.config }
  }

  setConfig(partial: Partial<AppConfig>): void {
    this.config = { ...this.config, ...partial }
    this.saveConfig()
  }
}
