import { homedir } from 'os'

/**
 * Expands a leading ~ in a path to the user's home directory.
 * Node.js doesn't auto-expand tildes like the shell does,
 * and the renderer sends literal '~' strings.
 */
export function expandTilde(p: string): string {
  if (p.startsWith('~/') || p === '~') {
    return p.replace('~', homedir())
  }
  return p
}
