#!/usr/bin/env python3
"""Convert a structured PR review markdown file to an interactive HTML report."""

import hashlib
import re
import sys
from html import escape
from pathlib import Path


def parse_frontmatter(text):
    """Extract YAML frontmatter as a dict."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not match:
        return {}, text
    fm = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            val = val.strip().strip('"').strip("'")
            fm[key.strip()] = val
    return fm, text[match.end():]


def parse_sections(text):
    """Split text into {heading: content} by ## headings."""
    sections = {}
    current = None
    lines = []
    for line in text.splitlines():
        m = re.match(r'^## (.+)$', line)
        if m:
            if current is not None:
                sections[current] = '\n'.join(lines).strip()
            current = m.group(1).strip()
            lines = []
        else:
            lines.append(line)
    if current is not None:
        sections[current] = '\n'.join(lines).strip()
    return sections


def parse_findings(text):
    """Parse ### ID. Title blocks into finding dicts."""
    findings = []
    # Split on ### headings
    parts = re.split(r'^### ', text, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        # First line: "C1. Title"
        heading = lines[0]
        m = re.match(r'^((?:C|I|M|S|R|BF-)\d+)\.\s+(.+)$', heading)
        if not m:
            continue
        finding = {
            'id': m.group(1),
            'title': m.group(2),
            'file': '',
            'bugfinder': '',
            'body': '',
            'labels': {},
        }
        rest = '\n'.join(lines[1:]).strip()
        # Extract **File**: `path`
        fm = re.match(r'^\*\*File\*\*:\s*`([^`]+)`\s*\n?', rest)
        if fm:
            finding['file'] = fm.group(1)
            rest = rest[fm.end():].strip()
        # Extract **Bugfinder**: Confirmed (BF-N) — must come before generic label pass
        bfm = re.match(r'^\*\*Bugfinder\*\*:\s*([^\n]+)', rest)
        if bfm:
            finding['bugfinder'] = bfm.group(1).strip()
            rest = rest[bfm.end():].strip()
        # Extract labeled fields: **Suggested change**: ..., **Trade-offs**: ..., etc.
        label_pattern = r'\*\*(\w[\w\- ]*)\*\*:\s*'
        label_positions = [(m.start(), m.end(), m.group(1)) for m in re.finditer(label_pattern, rest)]
        if label_positions:
            # Body is everything before the first label
            finding['body'] = rest[:label_positions[0][0]].strip()
            for i, (start, end, label) in enumerate(label_positions):
                next_start = label_positions[i + 1][0] if i + 1 < len(label_positions) else len(rest)
                finding['labels'][label.lower()] = rest[end:next_start].strip()
        else:
            finding['body'] = rest
        findings.append(finding)
    return findings


def parse_checklist(text):
    """Parse checklist bullet items into list of (label, status)."""
    items = []
    for line in text.splitlines():
        m = re.match(r'^-\s+(.+?):\s*(PASS|WARN|FAIL|N/A)\s*$', line.strip())
        if m:
            items.append((m.group(1), m.group(2)))
    return items


def parse_validation(text):
    """Parse validation stats into list of (label, value)."""
    items = []
    for line in text.splitlines():
        m = re.match(r'^-\s+(.+?):\s*(.+)$', line.strip())
        if m:
            items.append((m.group(1), m.group(2).strip()))
    return items


def parse_positives(text):
    """Parse positive bullet items into list of strings."""
    items = []
    for line in text.splitlines():
        m = re.match(r'^-\s+(.+)$', line.strip())
        if m:
            items.append(m.group(1))
    return items


def code_spans(text):
    """Convert `code` spans to <code> tags, escaping HTML."""
    parts = re.split(r'(`[^`]+`)', text)
    result = []
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            result.append(f'<code>{escape(part[1:-1], quote=False)}</code>')
        else:
            result.append(escape(part, quote=False))
    return ''.join(result)


def severity_class(finding_id):
    """Map finding ID prefix to CSS class."""
    if finding_id.startswith('C'):
        return 'critical'
    elif finding_id.startswith('I'):
        return 'important'
    elif finding_id.startswith('M'):
        return 'minor'
    elif finding_id.startswith('S'):
        return 'scope'
    elif finding_id.startswith('R'):
        return 'resolved'
    elif finding_id.startswith('BF-'):
        return 'critical'  # bugfinder findings use critical styling
    return 'minor'


def fix_label(finding):
    """Determine the action label for a finding."""
    for label in ['suggested change', 'fix', 'suggestion', 'alternative', 'action']:
        if label in finding['labels']:
            return 'Suggested change', finding['labels'][label]
    return None, None


def risk_class(score):
    """Map risk score to CSS class."""
    score = int(score)
    if score <= 3:
        return 'low'
    elif score <= 6:
        return 'moderate'
    else:
        return 'high'


def recommendation_label(rec):
    """Normalize recommendation to display text."""
    return {
        'approve': 'Approve',
        'request-changes': 'Request Changes',
        'needs-discussion': 'Needs Discussion',
    }.get(rec, rec)


def recommendation_class(rec):
    """Map recommendation to CSS class."""
    return {
        'approve': 'pass',
        'request-changes': 'fail',
        'needs-discussion': 'warn',
    }.get(rec, 'warn')


def parse_file_ref(file_ref):
    """Parse 'path:line' or 'path:start-end' into (path, start_line, end_line).

    Returns (path, start_line, end_line) where lines may be None.
    """
    if ':' not in file_ref:
        return file_ref, None, None
    path, line_part = file_ref.rsplit(':', 1)
    range_m = re.match(r'^(\d+)-(\d+)$', line_part)
    if range_m:
        return path, range_m.group(1), range_m.group(2)
    if line_part.isdigit():
        return path, line_part, None
    return file_ref, None, None


def github_file_url(pr_url, head_ref, file_ref):
    """Build a GitHub URL to a specific file and line in the PR files tab.

    Handles both 'path:line' and 'path:start-end' formats.
    Falls back to blob URL if pr_url doesn't contain a PR number.
    """
    if not pr_url or not file_ref:
        return None
    path, start_line, end_line = parse_file_ref(file_ref)
    m = re.match(r'(https://github\.com/[^/]+/[^/]+)/pull/(\d+)', pr_url)
    if not m:
        repo_m = re.match(r'(https://github\.com/[^/]+/[^/]+)', pr_url)
        if not repo_m or not head_ref:
            return None
        repo_base = repo_m.group(1)
        if start_line:
            url = f'{repo_base}/blob/{head_ref}/{path}#L{start_line}'
            if end_line:
                url += f'-L{end_line}'
            return url
        return f'{repo_base}/blob/{head_ref}/{path}'
    pr_files_url = f'{m.group(1)}/pull/{m.group(2)}/files'
    diff_hash = hashlib.sha256(path.encode()).hexdigest()
    if start_line:
        return f'{pr_files_url}#diff-{diff_hash}R{start_line}'
    return f'{pr_files_url}#diff-{diff_hash}'


def build_html(fm, sections):
    """Build the complete HTML string."""
    title = fm.get('title', 'PR Review')
    risk = fm.get('risk', '?')
    rec = fm.get('recommendation', 'needs-discussion')
    pr_url = fm.get('pr_url', '')
    head_ref = fm.get('head_ref', '')
    risk_cls = risk_class(risk) if risk != '?' else 'moderate'
    rec_cls = recommendation_class(rec)
    rec_label = recommendation_label(rec)

    # Parse all finding sections
    section_configs = [
        ('Critical Issues', 'critical'),
        ('Important Concerns', 'important'),
        ('Minor Suggestions', 'minor'),
        ('Scope Concerns', 'scope'),
    ]
    all_findings = {}
    counts = {}
    for section_name, css_class in section_configs:
        if section_name in sections:
            findings = parse_findings(sections[section_name])
            all_findings[section_name] = findings
            counts[css_class] = len(findings)
        else:
            all_findings[section_name] = []
            counts[css_class] = 0

    positives = parse_positives(sections.get('Positives', ''))
    checklist = parse_checklist(sections.get('Checklist', ''))
    validation = parse_validation(sections.get('Validation', ''))

    # Parse addressed external findings
    addressed_text = sections.get('Addressed External Findings', '')
    addressed_findings = []
    addressed_summary = ''
    if addressed_text:
        lines = addressed_text.strip().splitlines()
        # First non-empty line that doesn't start with ### is the summary
        rest_lines = []
        for line in lines:
            if not addressed_summary and not line.startswith('###') and line.strip():
                addressed_summary = line.strip()
            else:
                rest_lines.append(line)
        addressed_findings = parse_findings('\n'.join(rest_lines))

    # Build findings HTML
    findings_html = ''
    for section_name, css_class in section_configs:
        findings = all_findings[section_name]
        if not findings:
            continue
        findings_html += f'''
  <div class="findings-section">
    <div class="section-heading">
      <h2>{escape(section_name)}</h2>
      <span class="count {css_class}">{len(findings)}</span>
    </div>
'''
        for f in findings:
            sev = severity_class(f['id'])
            label_name, label_text = fix_label(f)
            tradeoffs = f['labels'].get('trade-offs', '')
            body_html = code_spans(f['body']) if f['body'] else ''
            # Wrap body paragraphs
            if body_html:
                paras = [p.strip() for p in body_html.split('\n\n') if p.strip()]
                body_html = ''.join(f'<p>{p}</p>' for p in paras)
                if not paras:
                    body_html = f'<p>{body_html}</p>'

            label_html = ''
            if label_name and label_text:
                label_html = f'''
        <div class="fix-label">{escape(label_name)}</div>
        <div class="fix-text">{code_spans(label_text)}</div>'''

            tradeoffs_html = ''
            if tradeoffs:
                tradeoffs_html = f'''
        <div class="tradeoffs">{code_spans(tradeoffs)}</div>'''

            file_url = github_file_url(pr_url, head_ref, f['file'])
            if file_url:
                file_html = f'<a class="finding-file" href="{escape(file_url)}" target="_blank" onclick="event.stopPropagation()">{escape(f["file"])}</a>'
            else:
                file_html = f'<div class="finding-file">{escape(f["file"])}</div>'

            bugfinder_badge = f'<span class="bugfinder-badge">Bugfinder</span>' if f.get('bugfinder') else ''
            tags_row_html = f'<div class="finding-tags">{bugfinder_badge}</div>' if bugfinder_badge else ''
            meta_html = f'<div class="finding-meta">{file_html}</div>'
            findings_html += f'''
    <div class="finding {sev}">
      <div class="finding-header" onclick="toggle(this.closest('.finding'))">
        <span class="finding-id">{escape(f['id'])}</span>
        <div class="finding-title-area">
          <div class="finding-title">{code_spans(f['title'])}</div>
          {tags_row_html}
          {meta_html}
        </div>
        <span class="finding-chevron">&#9654;</span>
      </div>
      <div class="finding-body">
        {body_html}{label_html}{tradeoffs_html}
      </div>
    </div>
'''
        findings_html += '  </div>\n'

    # Build positives HTML
    positives_html = ''
    if positives:
        items = '\n'.join(f'      <li>{code_spans(p)}</li>' for p in positives)
        positives_html = f'''
  <div class="positives">
    <h3>Positive Aspects</h3>
    <ul>
{items}
    </ul>
  </div>
'''

    # Build checklist HTML
    checklist_html = ''
    if checklist:
        items = '\n'.join(
            f'      <div class="check-item"><span class="label">{escape(label)}</span>'
            f'<span class="status {status.lower().replace("/", "")}">{escape(status)}</span></div>'
            for label, status in checklist
        )
        checklist_html = f'''
  <div class="checklist">
    <h2>Checklist</h2>
    <div class="checklist-grid">
{items}
    </div>
  </div>
'''

    # Build validation HTML
    validation_html = ''
    if validation:
        items = ''.join(f'<span>{escape(label)}: {escape(val)}</span>' for label, val in validation)
        validation_html = f'''
  <div class="validation">
    {items}
  </div>
'''

    # Build stat bar
    stat_items = []
    for css_class, label in [('critical', 'Critical'), ('important', 'Important'), ('minor', 'Minor'), ('scope', 'Scope')]:
        if counts.get(css_class, 0) > 0:
            stat_items.append(f'''
    <div class="stat">
      <div class="stat-dot {css_class}"></div>
      <span class="stat-count">{counts[css_class]}</span>
      <span class="stat-label">{label}</span>
    </div>''')
    if positives:
        stat_items.append(f'''
    <div class="stat">
      <div class="stat-dot positive"></div>
      <span class="stat-count">{len(positives)}</span>
      <span class="stat-label">Positives</span>
    </div>''')
    bugfinder_confirmed_count = sum(
        1 for findings_list in all_findings.values()
        for f in findings_list if f.get('bugfinder')
    )
    if bugfinder_confirmed_count > 0:
        stat_items.append(f'''
    <div class="stat">
      <div class="stat-dot bugfinder"></div>
      <span class="stat-count">{bugfinder_confirmed_count}</span>
      <span class="stat-label">Bugfinder confirmed</span>
    </div>''')
    stat_bar = '\n'.join(stat_items)

    # Assessment
    assessment_text = sections.get('Assessment', '')
    assessment_html = ''
    if assessment_text:
        assessment_html = f'''
  <div class="assessment">
    <h2>Overall Assessment</h2>
    <span class="recommendation {rec_cls}">{escape(rec_label)}</span>
    <p>{code_spans(assessment_text)}</p>
  </div>
'''

    # Addressed external findings (collapsed outer accordion with nested items)
    addressed_html = ''
    if addressed_findings:
        items_html = ''
        for f in addressed_findings:
            status = f['labels'].get('status', '')
            addr_file_url = github_file_url(pr_url, head_ref, f['file'])
            if addr_file_url:
                addr_file_html = f'<a class="finding-file" href="{escape(addr_file_url)}" target="_blank" onclick="event.stopPropagation()">{escape(f["file"])}</a>'
            else:
                addr_file_html = f'<div class="finding-file">{escape(f["file"])}</div>'
            items_html += f'''
        <div class="nested-finding resolved">
          <div class="nested-finding-header" onclick="event.stopPropagation(); toggle(this.closest('.nested-finding'))">
            <span class="finding-id">{escape(f['id'])}</span>
            <div class="finding-title-area">
              <div class="finding-title">{code_spans(f['title'])}</div>
              {addr_file_html}
            </div>
            <span class="finding-chevron">&#9654;</span>
          </div>
          <div class="nested-finding-body">
            <p class="resolved-status">{code_spans(status)}</p>
          </div>
        </div>
'''
        addressed_html = f'''
  <div class="addressed-accordion">
    <div class="addressed-header" onclick="toggle(this.closest('.addressed-accordion'))">
      <span class="finding-id" style="background: var(--resolved-badge);">{len(addressed_findings)}</span>
      <div class="finding-title-area">
        <div class="finding-title">Addressed External Findings</div>
        <div class="addressed-subtitle">{code_spans(addressed_summary)}</div>
      </div>
      <span class="finding-chevron">&#9654;</span>
    </div>
    <div class="addressed-body">
{items_html}
    </div>
  </div>
'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
{CSS}
</head>
<body>

<div class="theme-toggle" onclick="toggleTheme()">
  <div class="toggle-track">
    <span class="icon icon-sun">&#9728;</span>
    <span class="icon icon-moon">&#9790;</span>
    <div class="toggle-knob"></div>
  </div>
</div>

<div class="container">

  <div class="pr-header">
    <h1>{escape(title)}</h1>
    <div class="subtitle">PR Review{'&nbsp;&nbsp;<a href="' + escape(pr_url) + '" target="_blank" class="pr-link">View PR ↗</a>' if pr_url else ''}</div>
  </div>

  <div class="summary-section">
    <h2>Intent</h2>
    <p>{code_spans(sections.get('Intent', ''))}</p>
  </div>

  <div class="summary-section">
    <h2>Changes</h2>
    <p>{code_spans(sections.get('Changes', ''))}</p>
  </div>

  <div class="summary-section">
    <div class="risk-row">
      <div class="risk-badge {risk_cls}">{escape(str(risk))}</div>
      <div>
        <h2 style="margin-bottom: 2px">Risk</h2>
        <div class="risk-description">{code_spans(sections.get('Risk', ''))}</div>
      </div>
    </div>
  </div>

  <div class="divider"></div>

  <div class="summary-section">
    <h2>Results</h2>
    <p>{code_spans(sections.get('Results', ''))}</p>
  </div>

  <div class="stat-bar">
{stat_bar}
  </div>

{positives_html}

  <div class="controls">
    <button onclick="expandAll()">Expand all</button>
    <button onclick="collapseAll()">Collapse all</button>
  </div>

{findings_html}

{checklist_html}

{assessment_html}

{addressed_html}

{validation_html}

  <div class="disclaimer">
    Warning: This report was generated by AI, and AI can make mistakes. Make sure to verify these findings before acting on them.
  </div>

</div>

{JS}

</body>
</html>'''


CSS = '''<style>
  :root {
    --bg: #f5f5f7;
    --surface: #ffffff;
    --text: #2c2c2e;
    --text-muted: #86868b;
    --text-bright: #1d1d1f;
    --accent: #0071e3;
    --critical-bg: #fff5f5;
    --critical-border: #e53935;
    --critical-badge: #d32f2f;
    --important-bg: #fff8f0;
    --important-border: #ef6c00;
    --important-badge: #e65100;
    --minor-bg: #f0f7ff;
    --minor-border: #1976d2;
    --minor-badge: #1565c0;
    --scope-bg: #f5f0ff;
    --scope-border: #7b1fa2;
    --scope-badge: #6a1b9a;
    --resolved-bg: #f5f5f7;
    --resolved-border: #9e9e9e;
    --resolved-badge: #757575;
    --positive-bg: #f0faf0;
    --positive-border: #2e7d32;
    --pass: #2e7d32;
    --warn: #e65100;
    --fail: #c62828;
    --na: #86868b;
    --divider: #d2d2d7;
    --code-bg: #f0f0f2;
    --code-text: #0071e3;
    --radius: 8px;
    --hover-brighten: brightness(0.97);
    --tradeoffs-bg: rgba(0,0,0,0.03);
    --status-pass-bg: rgba(46, 125, 50, 0.08);
    --status-warn-bg: rgba(230, 81, 0, 0.08);
    --status-fail-bg: rgba(198, 40, 40, 0.08);
    --status-na-bg: rgba(134, 134, 139, 0.06);
    --toggle-bg: #e8e8ed;
    --toggle-knob: #ffffff;
  }
  [data-theme="dark"] {
    --bg: #1a1a2e;
    --surface: #16213e;
    --text: #e0e0e0;
    --text-muted: #8892a4;
    --text-bright: #ffffff;
    --accent: #4fc3f7;
    --critical-bg: #2d1b1b;
    --critical-border: #d32f2f;
    --critical-badge: #ef5350;
    --important-bg: #2d2518;
    --important-border: #f57c00;
    --important-badge: #ffb74d;
    --minor-bg: #1b2636;
    --minor-border: #42a5f5;
    --minor-badge: #64b5f6;
    --scope-bg: #251b36;
    --scope-border: #ab47bc;
    --scope-badge: #ce93d8;
    --resolved-bg: #1e2130;
    --resolved-border: #616161;
    --resolved-badge: #9e9e9e;
    --positive-bg: #1b2d1b;
    --positive-border: #388e3c;
    --pass: #66bb6a;
    --warn: #ffb74d;
    --fail: #ef5350;
    --na: #8892a4;
    --divider: #2a3a5c;
    --code-bg: #0d1b2a;
    --code-text: #4fc3f7;
    --radius: 8px;
    --hover-brighten: brightness(1.1);
    --tradeoffs-bg: rgba(255,255,255,0.03);
    --status-pass-bg: rgba(102, 187, 106, 0.12);
    --status-warn-bg: rgba(255, 183, 77, 0.12);
    --status-fail-bg: rgba(239, 83, 80, 0.12);
    --status-na-bg: rgba(136, 146, 164, 0.1);
    --toggle-bg: #2a3a5c;
    --toggle-knob: #e0e0e0;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6; padding: 0;
    transition: background 0.25s ease, color 0.25s ease;
  }
  .container { max-width: 860px; margin: 0 auto; padding: 32px 24px 64px; }
  .theme-toggle {
    position: fixed; top: 16px; right: 20px; z-index: 100;
    cursor: pointer; user-select: none; -webkit-user-select: none;
  }
  .toggle-track {
    width: 48px; height: 26px; background: var(--toggle-bg);
    border-radius: 13px; position: relative; transition: background 0.25s ease;
  }
  .toggle-knob {
    width: 20px; height: 20px; background: var(--toggle-knob); border-radius: 50%;
    position: absolute; top: 3px; left: 3px;
    transition: transform 0.25s ease, background 0.25s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
  [data-theme="dark"] .toggle-knob { transform: translateX(22px); }
  .toggle-track .icon { position: absolute; top: 5px; font-size: 0.75rem; line-height: 1; transition: opacity 0.25s ease; }
  .toggle-track .icon-sun { left: 6px; opacity: 0; }
  .toggle-track .icon-moon { right: 6px; opacity: 1; }
  [data-theme="dark"] .toggle-track .icon-sun { opacity: 1; }
  [data-theme="dark"] .toggle-track .icon-moon { opacity: 0; }
  .pr-header { margin-bottom: 32px; }
  .pr-header h1 { font-size: 1.5rem; font-weight: 600; color: var(--text-bright); margin-bottom: 4px; padding-right: 80px; }
  .pr-header .subtitle { color: var(--text-muted); font-size: 0.875rem; }
  .pr-header .pr-link { color: var(--accent); text-decoration: none; font-weight: 500; }
  .pr-header .pr-link:hover { text-decoration: underline; }
  .summary-section { margin-bottom: 24px; }
  .summary-section h2 { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 8px; }
  .summary-section p { color: var(--text); font-size: 0.9375rem; }
  .risk-row { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
  .risk-badge { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 50%; font-size: 1.125rem; font-weight: 700; color: #ffffff; flex-shrink: 0; }
  .risk-badge.low { background: linear-gradient(135deg, #388e3c, #43a047); }
  .risk-badge.moderate { background: linear-gradient(135deg, #f57c00, #ff9800); }
  .risk-badge.high { background: linear-gradient(135deg, #c62828, #e53935); }
  .risk-description { font-size: 0.9375rem; color: var(--text); }
  .divider { height: 1px; background: var(--divider); margin: 28px 0; }
  .stat-bar { display: flex; gap: 20px; margin-bottom: 28px; flex-wrap: wrap; }
  .stat { display: flex; align-items: center; gap: 6px; }
  .stat-count { font-size: 1.25rem; font-weight: 700; color: var(--text-bright); }
  .stat-label { font-size: 0.8125rem; color: var(--text-muted); }
  .stat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .stat-dot.critical { background: var(--critical-badge); }
  .stat-dot.important { background: var(--important-badge); }
  .stat-dot.minor { background: var(--minor-badge); }
  .stat-dot.scope { background: var(--scope-badge); }
  .stat-dot.positive { background: var(--pass); }
  .stat-dot.bugfinder { background: #ef4444; }
  .positives { background: var(--positive-bg); border-left: 3px solid var(--positive-border); border-radius: var(--radius); padding: 16px 20px; margin-bottom: 28px; }
  .positives h3 { font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--pass); margin-bottom: 10px; }
  .positives ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
  .positives li { font-size: 0.875rem; color: var(--text); padding-left: 16px; position: relative; }
  .positives li::before { content: '+'; position: absolute; left: 0; color: var(--pass); font-weight: 600; }
  .findings-section { margin-bottom: 8px; }
  .section-heading { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
  .section-heading h2 { font-size: 1rem; font-weight: 600; color: var(--text-bright); text-transform: none; letter-spacing: 0; }
  .section-heading .count { font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 10px; color: #ffffff; }
  .section-heading .count.critical { background: var(--critical-badge); }
  .section-heading .count.important { background: var(--important-badge); }
  .section-heading .count.minor { background: var(--minor-badge); }
  .section-heading .count.scope { background: var(--scope-badge); }
  .finding { border-radius: var(--radius); margin-bottom: 8px; overflow: hidden; }
  .finding.critical { background: var(--critical-bg); border: 1px solid var(--critical-border); }
  .finding.important { background: var(--important-bg); border: 1px solid var(--important-border); }
  .finding.minor { background: var(--minor-bg); border: 1px solid var(--minor-border); }
  .finding.scope { background: var(--scope-bg); border: 1px solid var(--scope-border); }
  .finding-header { display: flex; align-items: flex-start; gap: 12px; padding: 14px 18px; cursor: pointer; user-select: none; -webkit-user-select: none; }
  .finding-header:hover { filter: var(--hover-brighten); }
  .finding-id { font-size: 0.75rem; font-weight: 700; padding: 2px 7px; border-radius: 4px; color: #ffffff; flex-shrink: 0; margin-top: 1px; }
  .finding.critical .finding-id { background: var(--critical-badge); }
  .finding.important .finding-id { background: var(--important-badge); }
  .finding.minor .finding-id { background: var(--minor-badge); }
  .finding.scope .finding-id { background: var(--scope-badge); }
  .finding-title-area { flex: 1; min-width: 0; }
  .finding-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-bright); line-height: 1.4; }
  .finding-file { font-size: 0.8125rem; color: var(--text-muted); font-family: 'SF Mono', Menlo, Monaco, monospace; margin-top: 2px; display: block; }
  a.finding-file { text-decoration: none; color: var(--accent); cursor: pointer; display: inline; }
  a.finding-file:hover { text-decoration: underline; }
  .bugfinder-badge { display: inline-block; font-size: 0.6875rem; font-weight: 600; padding: 1px 7px; border-radius: 8px; background: #7f1d1d; color: #fca5a5; white-space: nowrap; margin-top: 3px; }
  [data-theme="light"] .bugfinder-badge { background: #fee2e2; color: #b91c1c; }
  .finding-tags { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; margin-top: 3px; }
  .finding-meta { margin-top: 2px; }
  .finding-chevron { color: var(--text-muted); font-size: 0.75rem; flex-shrink: 0; transition: transform 0.2s ease; margin-top: 4px; }
  .finding.open .finding-chevron { transform: rotate(90deg); }
  .finding-body { display: none; padding: 0 18px 16px 47px; }
  .finding.open .finding-body { display: block; }
  .finding-body p { font-size: 0.875rem; color: var(--text); margin-bottom: 12px; line-height: 1.65; }
  .finding-body .fix-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
  .finding.critical .fix-label { color: var(--critical-badge); }
  .finding.important .fix-label { color: var(--important-badge); }
  .finding.minor .fix-label { color: var(--minor-badge); }
  .finding.scope .fix-label { color: var(--scope-badge); }
  .finding-body .fix-text { font-size: 0.875rem; color: var(--text); line-height: 1.65; }
  .finding-body code { font-family: 'SF Mono', Menlo, Monaco, monospace; font-size: 0.8125rem; background: var(--code-bg); padding: 2px 6px; border-radius: 3px; color: var(--code-text); }
  .finding-body .tradeoffs { margin-top: 10px; padding: 10px 14px; background: var(--tradeoffs-bg); border-radius: 6px; font-size: 0.8125rem; color: var(--text-muted); font-style: italic; }
  .checklist { margin-top: 28px; margin-bottom: 28px; }
  .checklist h2 { font-size: 1rem; font-weight: 600; color: var(--text-bright); margin-bottom: 12px; }
  .checklist-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }
  .check-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; background: var(--surface); border-radius: 6px; font-size: 0.8125rem; }
  .check-item .label { color: var(--text-muted); }
  .check-item .status { font-weight: 600; font-size: 0.75rem; padding: 1px 8px; border-radius: 4px; }
  .status.pass { color: var(--pass); background: var(--status-pass-bg); }
  .status.warn { color: var(--warn); background: var(--status-warn-bg); }
  .status.fail { color: var(--fail); background: var(--status-fail-bg); }
  .status.na { color: var(--na); background: var(--status-na-bg); }
  .assessment { background: var(--surface); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 24px; }
  .assessment h2 { font-size: 1rem; font-weight: 600; color: var(--text-bright); margin-bottom: 6px; }
  .assessment .recommendation { display: inline-block; font-size: 0.8125rem; font-weight: 600; padding: 3px 10px; border-radius: 4px; margin-bottom: 10px; color: #ffffff; }
  .assessment .recommendation.pass { background: var(--pass); }
  .assessment .recommendation.warn { background: var(--warn); }
  .assessment .recommendation.fail { background: var(--fail); }
  .assessment p { font-size: 0.875rem; color: var(--text); line-height: 1.65; }
  .validation { font-size: 0.8125rem; color: var(--text-muted); display: flex; flex-wrap: wrap; gap: 6px 18px; }
  .validation span { white-space: nowrap; }
  .disclaimer { margin-top: 32px; padding: 16px 20px; background: var(--surface); border-radius: var(--radius); font-size: 0.8125rem; color: var(--text-muted); line-height: 1.6; font-style: italic; text-align: center; }
  .controls { display: flex; gap: 8px; margin-bottom: 16px; }
  .controls button { font-size: 0.75rem; font-weight: 500; padding: 4px 12px; border-radius: 4px; border: 1px solid var(--divider); background: var(--surface); color: var(--text-muted); cursor: pointer; transition: all 0.15s ease; }
  .controls button:hover { color: var(--text-bright); border-color: var(--text-muted); }
  .stat-dot.resolved { background: var(--resolved-badge); }
  .addressed-accordion {
    background: var(--resolved-bg); border: 1px solid var(--resolved-border);
    border-radius: var(--radius); margin-bottom: 8px; overflow: hidden;
  }
  .addressed-header {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 14px 18px; cursor: pointer; user-select: none; -webkit-user-select: none;
  }
  .addressed-header:hover { filter: var(--hover-brighten); }
  .addressed-subtitle { font-size: 0.8125rem; color: var(--text-muted); margin-top: 2px; }
  .addressed-body { display: none; padding: 0 14px 14px 14px; }
  .addressed-accordion.open .addressed-body { display: block; }
  .addressed-accordion.open > .addressed-header > .finding-chevron { transform: rotate(90deg); }
  .nested-finding {
    background: var(--surface); border: 1px solid var(--resolved-border);
    border-radius: 6px; margin-bottom: 6px; overflow: hidden;
  }
  .nested-finding-header {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px; cursor: pointer; user-select: none; -webkit-user-select: none;
  }
  .nested-finding-header:hover { filter: var(--hover-brighten); }
  .nested-finding .finding-id { background: var(--resolved-badge); font-size: 0.6875rem; padding: 1px 6px; }
  .nested-finding .finding-title { font-size: 0.8125rem; }
  .nested-finding .finding-file { font-size: 0.75rem; }
  .nested-finding-body { display: none; padding: 0 14px 12px 40px; }
  .nested-finding.open .nested-finding-body { display: block; }
  .nested-finding.open > .nested-finding-header > .finding-chevron { transform: rotate(90deg); }
  .nested-finding .resolved-status { color: var(--text-muted); font-style: italic; font-size: 0.8125rem; }
</style>'''

JS = '''<script>
function getPreferredTheme() {
  var stored = localStorage.getItem('pr-review-theme');
  if (stored) return stored;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('pr-review-theme', theme);
}
function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}
applyTheme(getPreferredTheme());
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
  if (!localStorage.getItem('pr-review-theme')) applyTheme(e.matches ? 'dark' : 'light');
});
function toggle(el) { el.classList.toggle('open'); }
function expandAll() { document.querySelectorAll('.finding').forEach(function(f) { f.classList.add('open'); }); }
function collapseAll() { document.querySelectorAll('.finding').forEach(function(f) { f.classList.remove('open'); }); }
</script>'''


def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <review.md> [output.html]')
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f'Error: {input_path} not found')
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    html = build_html(fm, sections)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.html')

    output_path.write_text(html, encoding='utf-8')
    print(output_path)


if __name__ == '__main__':
    main()
