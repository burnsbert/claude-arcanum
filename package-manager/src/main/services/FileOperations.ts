import { symlink, copyFile as fsCopyFile, mkdir, lstat, unlink, rm, cp, access } from 'fs/promises'
import { dirname } from 'path'

/**
 * Check whether a path exists without throwing.
 */
async function pathExists(p: string): Promise<boolean> {
  try {
    await access(p)
    return true
  } catch {
    return false
  }
}

/**
 * Creates a symlink from sourcePath to targetPath.
 * Automatically creates parent directories and detects source type (file/dir).
 */
export async function createSymlink(sourcePath: string, targetPath: string): Promise<void> {
  if (!(await pathExists(sourcePath))) {
    throw new Error(`Source does not exist: ${sourcePath}`)
  }
  if (await pathExists(targetPath)) {
    throw new Error(`Target already exists: ${targetPath}`)
  }

  await mkdir(dirname(targetPath), { recursive: true })

  const stat = await lstat(sourcePath)
  const type = stat.isDirectory() ? 'dir' : 'file'
  await symlink(sourcePath, targetPath, type)
}

/**
 * Copies a single file from sourcePath to targetPath.
 * Creates parent directories. Overwrites if target exists.
 */
export async function copyFile(sourcePath: string, targetPath: string): Promise<void> {
  await mkdir(dirname(targetPath), { recursive: true })
  await fsCopyFile(sourcePath, targetPath)
}

/**
 * Deep-copies a directory recursively from sourcePath to targetPath.
 */
export async function copyDirectory(sourcePath: string, targetPath: string): Promise<void> {
  await mkdir(dirname(targetPath), { recursive: true })
  await cp(sourcePath, targetPath, { recursive: true })
}

/**
 * Removes a file, symlink, or directory at the given path.
 * Uses lstat to detect symlinks without following them.
 */
export async function removeResource(targetPath: string): Promise<void> {
  const stat = await lstat(targetPath)

  if (stat.isSymbolicLink() || stat.isFile()) {
    await unlink(targetPath)
  } else if (stat.isDirectory()) {
    await rm(targetPath, { recursive: true })
  }
}
