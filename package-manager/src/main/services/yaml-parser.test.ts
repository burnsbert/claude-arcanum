import { describe, it, expect } from 'vitest'
import { parseFrontMatter } from './yaml-parser'

describe('parseFrontMatter', () => {
  it('parses valid YAML front matter', () => {
    const content = `---
name: test-agent
description: A test agent
model: sonnet
tools:
  - Read
  - Write
color: blue
---

# Body content here`

    const result = parseFrontMatter(content)
    expect(result.data.name).toBe('test-agent')
    expect(result.data.description).toBe('A test agent')
    expect(result.data.model).toBe('sonnet')
    expect(result.data.tools).toEqual(['Read', 'Write'])
    expect(result.data.color).toBe('blue')
    expect(result.body).toContain('# Body content here')
  })

  it('returns empty data for content without front matter', () => {
    const content = '# Just a markdown file\n\nNo front matter here.'
    const result = parseFrontMatter(content)
    expect(result.data).toEqual({})
    expect(result.body).toContain('# Just a markdown file')
  })

  it('handles empty content', () => {
    const result = parseFrontMatter('')
    expect(result.data).toEqual({})
    expect(result.body).toBe('')
  })

  it('parses command front matter with allowed-tools', () => {
    const content = `---
description: A command
allowed-tools: Bash, Read
argument-hint: <file>
---

Command body`

    const result = parseFrontMatter(content)
    expect(result.data.description).toBe('A command')
    expect(result.data['argument-hint']).toBe('<file>')
  })
})
