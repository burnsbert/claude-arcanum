import matter from 'gray-matter'

/**
 * Parses YAML front matter from markdown content.
 * Returns empty data object if front matter is absent or malformed.
 */
export function parseFrontMatter(fileContent: string): { data: Record<string, unknown>; body: string } {
  try {
    const result = matter(fileContent)
    return { data: result.data as Record<string, unknown>, body: result.content }
  } catch {
    return { data: {}, body: fileContent }
  }
}
