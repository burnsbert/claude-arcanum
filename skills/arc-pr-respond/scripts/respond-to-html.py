#!/usr/bin/env python3
"""Convert a structured PR respond markdown file to an interactive HTML report."""

import hashlib
import json
import re
import sys
from html import escape
from pathlib import Path


def load_feedback_sidecar(md_path):
    """Load the .feedback.json sidecar file if it exists.

    Returns a dict mapping comment_id (int) -> full item dict, or empty dict.
    """
    sidecar = Path(str(md_path).replace('.md', '.feedback.json'))
    if not sidecar.exists():
        # Also try without the .md replacement (in case path doesn't end in .md)
        sidecar = Path(str(md_path) + '.feedback.json')
    if not sidecar.exists():
        # Fallback: orchestrator may have skipped the cp step — try .fetch-pending.json
        code_reviews_dir = Path(md_path).parent
        pending = code_reviews_dir / '.fetch-pending.json'
        if pending.exists():
            sidecar = pending
    if not sidecar.exists():
        return {}
    try:
        data = json.loads(sidecar.read_text(encoding='utf-8'))
        lookup = {}
        for item in data.get('items', []):
            cid = item.get('comment_id')
            if cid is not None:
                lookup[cid] = item
        return lookup
    except (json.JSONDecodeError, KeyError):
        return {}


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
    parts = re.split(r'^### ', text, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        heading = lines[0]
        m = re.match(r'^((?:[A-Z]|BF-|H)\d+)\.\s+(.+)$', heading)
        if not m:
            continue
        finding = {
            'id': m.group(1),
            'title': m.group(2),
            'file': '',
            'comment_url': '',
            'comment_ids': [],
            'reviewers': '',
            'severity': '',
            'bugfinder': '',
            'reviewer_quotes': [],
            'additional_notes': '',
            'body': '',
            'labels': {},
            'recommended_action': '',
            'proposed_answer': '',
        }
        rest = '\n'.join(lines[1:]).strip()
        # Extract **File**: `path`
        fm = re.match(r'^\*\*File\*\*:\s*`([^`]+)`\s*\n?', rest)
        if fm:
            finding['file'] = fm.group(1)
            rest = rest[fm.end():].strip()
        # Extract **Comment**: url (direct link to PR comment)
        cm = re.match(r'^\*\*Comment\*\*:\s*(https?://\S+)\s*\n?', rest)
        if cm:
            finding['comment_url'] = cm.group(1)
            rest = rest[cm.end():].strip()
        # Extract **Comment IDs**: 12345,67890 (comma-separated ids for sidecar matching)
        cids_m = re.match(r'^\*\*Comment IDs?\*\*:\s*([^\n]+)', rest)
        if cids_m:
            try:
                finding['comment_ids'] = [int(x.strip()) for x in cids_m.group(1).split(',') if x.strip()]
            except ValueError:
                finding['comment_ids'] = []
            rest = rest[cids_m.end():].strip()
        # Extract **Reviewers**: Name1, Name2
        rm = re.match(r'^\*\*Reviewers?\*\*:\s*(.+?)\s*\n', rest)
        if rm:
            finding['reviewers'] = rm.group(1)
            rest = rest[rm.end():].strip()
        # Extract **Severity**: level
        sm = re.match(r'^\*\*Severity\*\*:\s*(\w+)\s*\n?', rest)
        if sm:
            finding['severity'] = sm.group(1)
            rest = rest[sm.end():].strip()
        # Extract **Bugfinder**: Confirmed (BF-N)
        bfm = re.match(r'^\*\*Bugfinder\*\*:\s*([^\n]+)', rest)
        if bfm:
            finding['bugfinder'] = bfm.group(1).strip()
            rest = rest[bfm.end():].strip()
        # Extract **Status**: for handled findings
        stm = re.match(r'^\*\*Status\*\*:\s*(.+?)(?:\n|$)', rest)
        if stm:
            finding['labels']['status'] = stm.group(1).strip()
            rest = rest[stm.end():].strip()
        # Extract blockquote reviewer comments (> **Name**: text)
        bq_lines = []
        non_bq_lines = []
        in_blockquote = False
        for line in rest.splitlines():
            if line.startswith('> ') or line == '>':
                bq_lines.append(line)
                in_blockquote = True
            elif in_blockquote and line.strip() == '':
                # End of blockquote
                in_blockquote = False
                non_bq_lines.append(line)
            else:
                in_blockquote = False
                non_bq_lines.append(line)
        if bq_lines:
            # Parse individual reviewer comments from blockquote
            # Preserve newlines for code blocks and structured content
            current_reviewer = None
            current_text = []
            for line in bq_lines:
                stripped = line[2:] if line.startswith('> ') else line[1:] if line.startswith('>') else line
                qm = re.match(r'\*\*(.+?)\*\*:\s*(.*)', stripped.strip())
                if qm and not stripped.strip().startswith('`'):
                    if current_reviewer:
                        finding['reviewer_quotes'].append({'reviewer': current_reviewer, 'text': '\n'.join(current_text)})
                    current_reviewer = qm.group(1)
                    current_text = [qm.group(2)] if qm.group(2) else []
                elif current_reviewer:
                    current_text.append(stripped.rstrip())
            if current_reviewer:
                finding['reviewer_quotes'].append({'reviewer': current_reviewer, 'text': '\n'.join(current_text)})
            rest = '\n'.join(non_bq_lines).strip()
        # Extract **Additional notes**: optional context
        an_match = re.search(r'\*\*Additional notes\*\*:\s*(.+?)(?:\n\n(?=\*\*)|$)', rest, re.DOTALL)
        if an_match:
            finding['additional_notes'] = an_match.group(1).strip()
            rest = rest[:an_match.start()] + rest[an_match.end():]
            rest = rest.strip()
        # Extract recommended action (inline text after **Recommended action**:)
        action_match = re.search(r'\*\*Recommended action\*\*:\s*(.+?)(?:\n\n|\n(?=\*\*)|$)', rest, re.DOTALL)
        if action_match:
            finding['recommended_action'] = action_match.group(1).strip()
            rest = rest[:action_match.start()] + rest[action_match.end():]
            rest = rest.strip()
        # Extract proposed answer (for question items)
        pa_match = re.search(r'\*\*Proposed answer\*\*:\s*(.+?)(?:\n\n|\n(?=\*\*)|$)', rest, re.DOTALL)
        if pa_match:
            finding['proposed_answer'] = pa_match.group(1).strip()
            rest = rest[:pa_match.start()] + rest[pa_match.end():]
            rest = rest.strip()
        # Extract labeled fields
        label_pattern = r'\*\*(\w[\w\- ]*)\*\*:\s*'
        label_positions = [(m.start(), m.end(), m.group(1)) for m in re.finditer(label_pattern, rest)]
        if label_positions:
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


# HTML tags allowed to pass through in reviewer comments
PASSTHROUGH_TAGS = re.compile(
    r'(</?(?:details|summary|blockquote)(?:\s[^>]*)?>)',
    re.IGNORECASE,
)



def esc(text):
    """HTML-escape text content without escaping single quotes (only needed in attributes)."""
    return escape(text, quote=False)


def render_original_comment(text):
    """Render a full original reviewer comment with all sections expanded.

    Converts <details>/<summary> into flat visible sections with styled headers
    instead of collapsible elements. Everything is visible at once.
    """
    # Strip <details> and </details> tags entirely
    text = re.sub(r'<details>\s*', '', text)
    text = re.sub(r'</details>\s*', '', text)
    # Convert <summary>Title</summary> into a styled section header
    text = re.sub(r'<summary>(.*?)</summary>\s*', r'**\1**\n', text)
    return render_reviewer_markdown(text)


def render_reviewer_markdown(text):
    """Render reviewer comment text to HTML with richer markdown support.

    Handles fenced code blocks (``` or `` since LLMs sometimes mangle triple backticks),
    <details>/<summary> HTML passthrough, bold, and inline code spans.
    """
    # Phase 1: extract fenced code blocks before escaping anything
    # Match ```lang or ``lang (2+ backticks) as opening fence
    code_blocks = []
    def replace_code_block(m):
        lang = m.group(1) or ''
        code = m.group(2)
        placeholder = f'\x00CODEBLOCK{len(code_blocks)}\x00'
        lang_attr = f' class="language-{escape(lang)}"' if lang.strip() else ''
        code_blocks.append(f'<pre><code{lang_attr}>{escape(code.strip())}</code></pre>')
        return placeholder

    # Match 2+ backticks as fence (handles both ``` and `` from LLM mangling)
    text = re.sub(r'`{2,}(\w*)\n(.*?)`{2,}', replace_code_block, text, flags=re.DOTALL)

    # Phase 1.5: convert markdown blockquotes (> lines) to <blockquote> HTML
    bq_lines = []
    out_lines = []
    for line in text.split('\n'):
        if line.startswith('> '):
            bq_lines.append(line[2:])
        elif line == '>':
            bq_lines.append('')
        else:
            if bq_lines:
                out_lines.append('<blockquote>' + '\n'.join(bq_lines) + '</blockquote>')
                bq_lines = []
            out_lines.append(line)
    if bq_lines:
        out_lines.append('<blockquote>' + '\n'.join(bq_lines) + '</blockquote>')
    text = '\n'.join(out_lines)

    # Phase 2: split on passthrough HTML tags so we don't escape them
    parts = PASSTHROUGH_TAGS.split(text)
    rendered = []
    for part in parts:
        if PASSTHROUGH_TAGS.fullmatch(part):
            rendered.append(part)
        else:
            # Bold
            segment = re.sub(r'\*\*(.+?)\*\*', lambda m: f'<strong>{esc(m.group(1))}</strong>', part)
            # Italic (underscore style - common in CodeRabbit: _emoji text_)
            segment = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', lambda m: f'<em>{esc(m.group(1))}</em>', segment)
            # Inline code spans
            segment = re.sub(r'`([^`]+)`', lambda m: f'<code>{esc(m.group(1))}</code>', segment)
            # Escape remaining text (but not the <strong> and <code> we just inserted)
            pieces = re.split(r'(</?(?:strong|code|em)[^>]*>)', segment)
            escaped = []
            for piece in pieces:
                if re.fullmatch(r'</?(?:strong|code|em)[^>]*>', piece):
                    escaped.append(piece)
                else:
                    escaped.append(esc(piece))
            rendered.append(''.join(escaped))

    result = ''.join(rendered)

    # Phase 3: restore code block placeholders
    for i, block in enumerate(code_blocks):
        result = result.replace(f'\x00CODEBLOCK{i}\x00', block)

    return result


def severity_class(finding):
    """Map finding severity or ID prefix to CSS class."""
    sev = finding.get('severity', '').lower()
    if sev in ('critical', 'important', 'minor', 'nitpick', 'invalid'):
        return sev
    fid = finding.get('id', '')
    if fid.startswith('BF-'):
        return 'critical'
    if fid.startswith('H'):
        return 'handled'
    if fid.startswith('Q'):
        return 'question'
    if fid.startswith('P'):
        return 'positive'
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


def reviewer_tags_html(reviewers_str):
    """Build HTML for reviewer tag pills from a comma-separated string."""
    if not reviewers_str:
        return ''
    tags = [r.strip() for r in reviewers_str.split(',') if r.strip()]
    pills = ''.join(f'<span class="reviewer-tag">{escape(t)}</span>' for t in tags)
    return f'<div class="reviewer-tags">{pills}</div>'


def build_html(fm, sections, feedback_lookup=None):
    """Build the complete HTML string."""
    title = fm.get('title', 'PR Respond')
    risk = fm.get('risk', '?')
    rec = fm.get('recommendation', 'needs-discussion')
    pr_url = fm.get('pr_url', '')
    head_ref = fm.get('head_ref', '')
    risk_cls = risk_class(risk) if risk != '?' else 'moderate'
    rec_cls = recommendation_class(rec)
    rec_label = recommendation_label(rec)

    # Parse all finding sections
    section_configs = [
        ('Critical Feedback', 'critical'),
        ('Important Feedback', 'important'),
        ('Minor Feedback', 'minor'),
        ('Nitpick Feedback', 'nitpick'),
        ('Invalid Feedback', 'invalid'),
        ('Question Feedback', 'question'),
        ('Positive Comments', 'positive'),
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

    checklist = parse_checklist(sections.get('Checklist', ''))
    validation = parse_validation(sections.get('Validation', ''))

    # Parse handled feedback
    handled_text = sections.get('Handled Feedback', '')
    handled_findings = []
    handled_summary = ''
    if handled_text:
        lines = handled_text.strip().splitlines()
        rest_lines = []
        for line in lines:
            if not handled_summary and not line.startswith('###') and line.strip():
                handled_summary = line.strip()
            else:
                rest_lines.append(line)
        handled_findings = parse_findings('\n'.join(rest_lines))

    # Build findings HTML
    matched_cids = set()  # Track which original comments got matched to findings
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
            sev = severity_class(f)
            label_name, label_text = fix_label(f)
            tradeoffs = f['labels'].get('trade-offs', '')
            # Build reviewer quotes HTML
            reviewer_quotes_html = ''
            if f['reviewer_quotes']:
                quotes_items = ''
                for rq in f['reviewer_quotes']:
                    quotes_items += f'''
            <div class="reviewer-quote">
              <div class="quote-author">{escape(rq["reviewer"])}</div>
              <div class="quote-text">{render_reviewer_markdown(rq["text"])}</div>
            </div>'''
                reviewer_quotes_html = f'''
        <div class="reviewer-quotes">{quotes_items}
        </div>'''

            # Build additional notes HTML
            notes_html = ''
            if f['additional_notes']:
                notes_html = f'''
        <div class="additional-notes">
          <div class="notes-label">Additional Notes</div>
          <div class="notes-text">{code_spans(f["additional_notes"])}</div>
        </div>'''

            body_html = code_spans(f['body']) if f['body'] else ''
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

            action_html = ''
            if f['recommended_action'] and sev not in ('question', 'positive'):
                action_html = f'''
        <div class="recommended-action">
          <div class="action-label">Recommended Action</div>
          <div class="action-text">{code_spans(f["recommended_action"])}</div>
        </div>'''

            proposed_answer_html = ''
            if f['proposed_answer'] and sev == 'question':
                proposed_answer_html = f'''
        <div class="proposed-answer">
          <div class="action-label">Proposed Answer</div>
          <div class="action-text">{code_spans(f["proposed_answer"])}</div>
        </div>'''

            # Build original comment expandable section from sidecar data
            original_html = ''
            if feedback_lookup:
                originals = []
                f_file = f.get('file', '')
                f_line_start = None
                f_line_end = None
                if f_file and ':' in f_file:
                    f_path, f_line_part = f_file.rsplit(':', 1)
                    range_m = re.match(r'^(\d+)-(\d+)$', f_line_part)
                    single_m = re.match(r'^(\d+)$', f_line_part)
                    if range_m:
                        f_line_start = int(range_m.group(1))
                        f_line_end = int(range_m.group(2))
                        f_file = f_path
                    elif single_m:
                        f_line_start = int(single_m.group(1))
                        f_line_end = f_line_start
                        f_file = f_path

                # Priority 1: explicit comment_ids list written by orchestrator
                cids = f.get('comment_ids', [])
                # Priority 2: extract from comment_url (#discussion_r<id>)
                if not cids:
                    cid_match = re.search(r'#discussion_r(\d+)', f.get('comment_url', ''))
                    if cid_match:
                        cids = [int(cid_match.group(1))]

                # Try ID-based matching (works even when no file field, e.g. Q/P findings)
                if cids:
                    originals = [feedback_lookup[cid] for cid in cids if cid in feedback_lookup]

                # Fallback to file+range overlap when IDs matched nothing (LLM may hallucinate IDs)
                # Only match when both finding and comment have line info — file-only is too broad
                if not originals and f_file and f_line_start:
                    for cid, item in feedback_lookup.items():
                        if item.get('file') == f_file:
                            item_line = item.get('line')
                            item_start = item.get('start_line') or item_line
                            if item_line:
                                ranges_overlap = (f_line_start <= item_line
                                                  and item_start <= (f_line_end or f_line_start))
                                if ranges_overlap:
                                    originals.append(item)

                if originals:
                    for orig in originals:
                        ocid = orig.get('comment_id')
                        if ocid is not None:
                            matched_cids.add(ocid)
                    orig_items = ''
                    for orig in originals:
                        reviewer = orig.get('reviewer_display') or orig.get('reviewer') or 'Reviewer'
                        body = orig.get('body', '')
                        # Strip CodeRabbit fingerprint/meta HTML comments
                        body = re.sub(r'<!--\s*fingerprinting:[^>]*-->', '', body)
                        body = re.sub(r'<!--\s*This is an auto-generated comment[^>]*-->', '', body)
                        body = re.sub(r'<!--\s*suggestion_start\s*-->', '', body)
                        body = re.sub(r'<!--\s*suggestion_end\s*-->', '', body)
                        body = body.strip()
                        orig_items += f'''
              <div class="original-comment">
                <div class="original-author">{escape(reviewer, quote=False)}</div>
                <div class="original-text">{render_original_comment(body)}</div>
              </div>'''
                    original_html = f'''
        <div class="original-section">
          <div class="original-header" onclick="event.stopPropagation(); toggle(this.closest('.original-section'))">
            <span class="original-label">Original Comment{"s" if len(originals) > 1 else ""}</span>
            <span class="finding-chevron">&#9654;</span>
          </div>
          <div class="original-body">{orig_items}
          </div>
        </div>'''

            comment_url = f['comment_url']
            # For inline code comments, link to Files changed tab instead of Conversation tab
            if comment_url and '#discussion_r' in comment_url and f['file']:
                comment_url = comment_url.replace('#discussion_r', '/files#r')
            file_url = comment_url or github_file_url(pr_url, head_ref, f['file'])
            if file_url:
                file_html = f'<a class="finding-file" href="{escape(file_url)}" target="_blank" onclick="event.stopPropagation()">{escape(f["file"])}</a>'
            else:
                file_html = f'<div class="finding-file">{escape(f["file"])}</div>' if f['file'] else ''

            tags_html = reviewer_tags_html(f['reviewers'])
            bugfinder_badge = f'<span class="bugfinder-badge">Bugfinder</span>' if f.get('bugfinder') else ''
            has_tags = bool(f.get('reviewers', '').strip()) or bool(f.get('bugfinder'))
            tags_row_html = f'<div class="finding-tags">{tags_html}{bugfinder_badge}</div>' if has_tags else ''
            meta_html = f'<div class="finding-meta">{file_html}</div>' if file_html else ''

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
        {reviewer_quotes_html}{notes_html}{body_html}{label_html}{tradeoffs_html}{action_html}{proposed_answer_html}{original_html}
      </div>
    </div>
'''
        findings_html += '  </div>\n'

    # Track handled findings' comment IDs so they don't appear in unmatched
    if feedback_lookup:
        for f in handled_findings:
            for cid in f.get('comment_ids', []):
                if cid in feedback_lookup:
                    matched_cids.add(cid)
            cid_match = re.search(r'#discussion_r(\d+)', f.get('comment_url', ''))
            if cid_match:
                cid_val = int(cid_match.group(1))
                if cid_val in feedback_lookup:
                    matched_cids.add(cid_val)

    # Build unmatched comments section
    unmatched_html = ''
    if feedback_lookup:
        unmatched = [
            (cid, item) for cid, item in feedback_lookup.items()
            if cid not in matched_cids
        ]
        if unmatched:
            unmatched_items = ''
            for cid, item in unmatched:
                reviewer = item.get('reviewer_display') or item.get('reviewer') or 'Reviewer'
                body = item.get('body', '')
                body = re.sub(r'<!--\s*fingerprinting:[^>]*-->', '', body)
                body = re.sub(r'<!--\s*This is an auto-generated comment[^>]*-->', '', body)
                body = re.sub(r'<!--\s*suggestion_start\s*-->', '', body)
                body = re.sub(r'<!--\s*suggestion_end\s*-->', '', body)
                body = body.strip()
                file_ref = item.get('file', '')
                line_ref = item.get('line')
                if file_ref and line_ref:
                    file_ref = f'{file_ref}:{line_ref}'
                url = item.get('url', '')
                if url and file_ref:
                    file_label = f'<a class="finding-file" href="{escape(url)}" target="_blank" onclick="event.stopPropagation()">{escape(file_ref)}</a>'
                elif file_ref:
                    file_label = f'<span class="finding-file">{escape(file_ref)}</span>'
                elif url:
                    file_label = f'<a class="finding-file" href="{escape(url)}" target="_blank" onclick="event.stopPropagation()">View comment</a>'
                else:
                    file_label = ''
                unmatched_items += f'''
      <div class="original-comment">
        <div class="original-author">{escape(reviewer, quote=False)}</div>
        {f'<div class="original-file">{file_label}</div>' if file_label else ''}
        <div class="original-text">{render_original_comment(body)}</div>
      </div>'''
            unmatched_html = f'''
  <div class="findings-section">
    <div class="section-heading">
      <h2>Unmatched Comments</h2>
      <span class="count handled">{len(unmatched)}</span>
    </div>
    <div class="finding handled">
      <div class="finding-header" onclick="toggle(this.closest('.finding'))">
        <span class="finding-id">...</span>
        <div class="finding-title-area">
          <div class="finding-title">Original comments not matched to any finding above</div>
        </div>
        <span class="finding-chevron">&#9654;</span>
      </div>
      <div class="finding-body">{unmatched_items}
      </div>
    </div>
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
    for css_class, label in [('critical', 'Critical'), ('important', 'Important'), ('minor', 'Minor'), ('nitpick', 'Nitpick'), ('invalid', 'Invalid'), ('question', 'Question'), ('positive', 'Positive')]:
        if counts.get(css_class, 0) > 0:
            stat_items.append(f'''
    <div class="stat">
      <div class="stat-dot {css_class}"></div>
      <span class="stat-count">{counts[css_class]}</span>
      <span class="stat-label">{label}</span>
    </div>''')
    if handled_findings:
        stat_items.append(f'''
    <div class="stat">
      <div class="stat-dot handled"></div>
      <span class="stat-count">{len(handled_findings)}</span>
      <span class="stat-label">Handled</span>
    </div>''')
    bugfinder_confirmed_count = sum(
        1 for findings_list in all_findings.values()
        for f in findings_list if f.get('bugfinder')
    ) + sum(1 for f in handled_findings if f.get('bugfinder'))
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

    # Handled feedback (collapsed outer accordion with nested items)
    handled_html = ''
    if handled_findings:
        items_html = ''
        for f in handled_findings:
            status = f['labels'].get('status', '')
            reviewer = f.get('reviewers', '')
            addr_file_url = github_file_url(pr_url, head_ref, f['file'])
            if addr_file_url:
                addr_file_html = f'<a class="finding-file" href="{escape(addr_file_url)}" target="_blank" onclick="event.stopPropagation()">{escape(f["file"])}</a>'
            else:
                addr_file_html = f'<div class="finding-file">{escape(f["file"])}</div>' if f['file'] else ''
            reviewer_html = f'<div class="handled-reviewer">{escape(reviewer)}</div>' if reviewer else ''
            items_html += f'''
        <div class="nested-finding handled">
          <div class="nested-finding-header" onclick="event.stopPropagation(); toggle(this.closest('.nested-finding'))">
            <span class="finding-id">{escape(f['id'])}</span>
            <div class="finding-title-area">
              <div class="finding-title">{code_spans(f['title'])}</div>
              {reviewer_html}
              {addr_file_html}
            </div>
            <span class="finding-chevron">&#9654;</span>
          </div>
          <div class="nested-finding-body">
            <p class="resolved-status">{code_spans(status)}</p>
          </div>
        </div>
'''
        handled_html = f'''
  <div class="addressed-accordion">
    <div class="addressed-header" onclick="toggle(this.closest('.addressed-accordion'))">
      <span class="finding-id" style="background: var(--handled-badge);">{len(handled_findings)}</span>
      <div class="finding-title-area">
        <div class="finding-title">Handled Feedback</div>
        <div class="addressed-subtitle">{code_spans(handled_summary)}</div>
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
    <div class="subtitle">PR Feedback Analysis{'&nbsp;&nbsp;<a href="' + escape(pr_url) + '" target="_blank" class="pr-link">View PR ↗</a>' if pr_url else ''}</div>
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

  <div class="controls">
    <button onclick="expandAll()">Expand all</button>
    <button onclick="collapseAll()">Collapse all</button>
  </div>

{findings_html}

{checklist_html}

{assessment_html}

{handled_html}

{unmatched_html}

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
    --nitpick-bg: #f0f7f7;
    --nitpick-border: #00897b;
    --nitpick-badge: #00796b;
    --invalid-bg: #f5f5f5;
    --invalid-border: #9e9e9e;
    --invalid-badge: #757575;
    --handled-bg: #f5f5f7;
    --handled-border: #9e9e9e;
    --handled-badge: #757575;
    --question-bg: #f5f0ff;
    --question-border: #7b1fa2;
    --question-badge: #6a1b9a;
    --positive-bg: #f1f8f1;
    --positive-border: #388e3c;
    --positive-badge: #2e7d32;
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
    --draft-bg: rgba(0,113,227,0.04);
    --draft-border: rgba(0,113,227,0.2);
    --status-pass-bg: rgba(46, 125, 50, 0.08);
    --status-warn-bg: rgba(230, 81, 0, 0.08);
    --status-fail-bg: rgba(198, 40, 40, 0.08);
    --status-na-bg: rgba(134, 134, 139, 0.06);
    --toggle-bg: #e8e8ed;
    --toggle-knob: #ffffff;
    --tag-bg: rgba(0,0,0,0.06);
    --tag-text: #555;
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
    --nitpick-bg: #1b2d2d;
    --nitpick-border: #26a69a;
    --nitpick-badge: #4db6ac;
    --invalid-bg: #1e2130;
    --invalid-border: #616161;
    --invalid-badge: #9e9e9e;
    --handled-bg: #1e2130;
    --handled-border: #616161;
    --handled-badge: #9e9e9e;
    --question-bg: #241b2d;
    --question-border: #9c27b0;
    --question-badge: #ce93d8;
    --positive-bg: #1b2d1b;
    --positive-border: #43a047;
    --positive-badge: #81c784;
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
    --draft-bg: rgba(79,195,247,0.06);
    --draft-border: rgba(79,195,247,0.2);
    --status-pass-bg: rgba(102, 187, 106, 0.12);
    --status-warn-bg: rgba(255, 183, 77, 0.12);
    --status-fail-bg: rgba(239, 83, 80, 0.12);
    --status-na-bg: rgba(136, 146, 164, 0.1);
    --toggle-bg: #2a3a5c;
    --toggle-knob: #e0e0e0;
    --tag-bg: rgba(255,255,255,0.08);
    --tag-text: #b0b0b0;
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
  .stat-dot.nitpick { background: var(--nitpick-badge); }
  .stat-dot.invalid { background: var(--invalid-badge); }
  .stat-dot.handled { background: var(--handled-badge); }
  .stat-dot.question { background: var(--question-badge); }
  .stat-dot.positive { background: var(--positive-badge); }
  .stat-dot.bugfinder { background: #ef4444; }
  .findings-section { margin-bottom: 8px; }
  .section-heading { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
  .section-heading h2 { font-size: 1rem; font-weight: 600; color: var(--text-bright); text-transform: none; letter-spacing: 0; }
  .section-heading .count { font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 10px; color: #ffffff; }
  .section-heading .count.critical { background: var(--critical-badge); }
  .section-heading .count.important { background: var(--important-badge); }
  .section-heading .count.minor { background: var(--minor-badge); }
  .section-heading .count.nitpick { background: var(--nitpick-badge); }
  .section-heading .count.invalid { background: var(--invalid-badge); }
  .section-heading .count.question { background: var(--question-badge); }
  .section-heading .count.positive { background: var(--positive-badge); }
  .section-heading .count.handled { background: var(--handled-badge); }
  .finding { border-radius: var(--radius); margin-bottom: 8px; overflow: hidden; }
  .finding.critical { background: var(--critical-bg); border: 1px solid var(--critical-border); }
  .finding.important { background: var(--important-bg); border: 1px solid var(--important-border); }
  .finding.minor { background: var(--minor-bg); border: 1px solid var(--minor-border); }
  .finding.nitpick { background: var(--nitpick-bg); border: 1px solid var(--nitpick-border); }
  .finding.invalid { background: var(--invalid-bg); border: 1px solid var(--invalid-border); }
  .finding.question { background: var(--question-bg); border: 1px solid var(--question-border); }
  .finding.positive { background: var(--positive-bg); border: 1px solid var(--positive-border); }
  .finding.handled { background: var(--handled-bg); border: 1px solid var(--handled-border); }
  .finding-header { display: flex; align-items: flex-start; gap: 12px; padding: 14px 18px; cursor: pointer; user-select: none; -webkit-user-select: none; }
  .finding-header:hover { filter: var(--hover-brighten); }
  .finding-id { font-size: 0.75rem; font-weight: 700; padding: 2px 7px; border-radius: 4px; color: #ffffff; flex-shrink: 0; margin-top: 1px; }
  .finding.critical .finding-id { background: var(--critical-badge); }
  .finding.important .finding-id { background: var(--important-badge); }
  .finding.minor .finding-id { background: var(--minor-badge); }
  .finding.nitpick .finding-id { background: var(--nitpick-badge); }
  .finding.invalid .finding-id { background: var(--invalid-badge); }
  .finding.question .finding-id { background: var(--question-badge); }
  .finding.positive .finding-id { background: var(--positive-badge); }
  .finding.handled .finding-id { background: var(--handled-badge); }
  .finding-title-area { flex: 1; min-width: 0; }
  .finding-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-bright); line-height: 1.4; }
  .finding-file { font-size: 0.8125rem; color: var(--text-muted); font-family: 'SF Mono', Menlo, Monaco, monospace; margin-top: 2px; display: block; }
  a.finding-file { text-decoration: none; color: var(--accent); cursor: pointer; display: inline; }
  a.finding-file:hover { text-decoration: underline; }
  .finding-chevron { color: var(--text-muted); font-size: 0.75rem; flex-shrink: 0; transition: transform 0.2s ease; margin-top: 4px; }
  .finding.open .finding-chevron { transform: rotate(90deg); }
  .finding-body { display: none; padding: 0 18px 16px 47px; }
  .finding.open .finding-body { display: block; }
  .finding-body p { font-size: 0.875rem; color: var(--text); margin-bottom: 12px; line-height: 1.65; }
  .finding-body .fix-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
  .finding.critical .fix-label { color: var(--critical-badge); }
  .finding.important .fix-label { color: var(--important-badge); }
  .finding.minor .fix-label { color: var(--minor-badge); }
  .finding.nitpick .fix-label { color: var(--nitpick-badge); }
  .finding.invalid .fix-label { color: var(--invalid-badge); }
  .finding.question .fix-label { color: var(--question-badge); }
  .finding.positive .fix-label { color: var(--positive-badge); }
  .finding-body .fix-text { font-size: 0.875rem; color: var(--text); line-height: 1.65; }
  .finding-body code { font-family: 'SF Mono', Menlo, Monaco, monospace; font-size: 0.8125rem; background: var(--code-bg); padding: 2px 6px; border-radius: 3px; color: var(--code-text); }
  .finding-body .tradeoffs { margin-top: 10px; padding: 10px 14px; background: var(--tradeoffs-bg); border-radius: 6px; font-size: 0.8125rem; color: var(--text-muted); font-style: italic; }
  .reviewer-quotes { margin-bottom: 14px; border-left: 3px solid var(--divider); padding-left: 14px; }
  .reviewer-quote { margin-bottom: 10px; }
  .reviewer-quote:last-child { margin-bottom: 0; }
  .quote-author { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); margin-bottom: 2px; }
  .quote-text { font-size: 0.875rem; color: var(--text); line-height: 1.6; }
  .quote-text pre { margin: 10px 0; padding: 12px 14px; background: var(--code-bg); border-radius: 6px; overflow-x: auto; }
  .quote-text pre code { font-family: 'SF Mono', Menlo, Monaco, monospace; font-size: 0.8125rem; color: var(--text); background: none; padding: 0; }
  .quote-text details { margin: 10px 0; }
  .quote-text summary { cursor: pointer; font-weight: 600; font-size: 0.8125rem; color: var(--text-muted); }
  .original-section { margin-top: 14px; border: 1px solid var(--divider); border-radius: 6px; overflow: hidden; }
  .original-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; background: var(--tradeoffs-bg); cursor: pointer; user-select: none; -webkit-user-select: none; }
  .original-header:hover { filter: var(--hover-brighten); }
  .original-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
  .original-body { display: none; padding: 12px 14px; }
  .original-section.open .original-body { display: block; }
  .original-section.open > .original-header > .finding-chevron { transform: rotate(90deg); }
  .original-comment { margin-bottom: 14px; border-left: 2px solid var(--divider); padding-left: 12px; }
  .original-comment:last-child { margin-bottom: 0; }
  .original-author { font-size: 0.6875rem; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
  .original-file { font-size: 0.75rem; margin-bottom: 4px; }
  .original-file .finding-file { font-size: 0.75rem; }
  .original-text { font-size: 0.8125rem; color: var(--text); line-height: 1.6; }
  .original-text pre { margin: 8px 0; padding: 10px 12px; background: var(--code-bg); border-radius: 4px; overflow-x: auto; }
  .original-text pre code { font-family: 'SF Mono', Menlo, Monaco, monospace; font-size: 0.75rem; color: var(--text); background: none; padding: 0; }
  .original-text code { font-family: 'SF Mono', Menlo, Monaco, monospace; font-size: 0.75rem; background: var(--code-bg); padding: 1px 4px; border-radius: 3px; color: var(--code-text); }
  .original-text details { margin: 8px 0; }
  .original-text summary { cursor: pointer; font-weight: 600; font-size: 0.75rem; color: var(--text-muted); }
  .original-text blockquote { margin: 8px 0; padding: 8px 12px; border-left: 3px solid var(--divider); background: var(--tradeoffs-bg); border-radius: 0 4px 4px 0; font-size: 0.8125rem; }
  .original-text em { font-style: italic; }
  .additional-notes { margin-bottom: 14px; padding: 10px 14px; background: var(--tradeoffs-bg); border-radius: 6px; }
  .notes-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 4px; }
  .notes-text { font-size: 0.875rem; color: var(--text); line-height: 1.6; }
  .reviewer-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 3px; }
  .reviewer-tag { font-size: 0.6875rem; font-weight: 500; padding: 1px 7px; border-radius: 8px; background: var(--tag-bg); color: var(--tag-text); white-space: nowrap; }
  .bugfinder-badge { display: inline-block; font-size: 0.6875rem; font-weight: 600; padding: 1px 7px; border-radius: 8px; background: #7f1d1d; color: #fca5a5; white-space: nowrap; }
  [data-theme="light"] .bugfinder-badge { background: #fee2e2; color: #b91c1c; }
  .finding-tags { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; margin-top: 3px; }
  .finding-meta { margin-top: 2px; }
  .recommended-action, .proposed-answer { margin-top: 14px; }
  .action-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); margin-bottom: 4px; }
  .finding.question .proposed-answer .action-label { color: var(--question-badge); }
  .action-text { font-size: 0.875rem; color: var(--text); line-height: 1.6; padding: 8px 14px; background: var(--draft-bg); border-left: 3px solid var(--draft-border); border-radius: 0 6px 6px 0; }
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
  .addressed-accordion {
    background: var(--handled-bg); border: 1px solid var(--handled-border);
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
    background: var(--surface); border: 1px solid var(--handled-border);
    border-radius: 6px; margin-bottom: 6px; overflow: hidden;
  }
  .nested-finding-header {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px; cursor: pointer; user-select: none; -webkit-user-select: none;
  }
  .nested-finding-header:hover { filter: var(--hover-brighten); }
  .nested-finding .finding-id { background: var(--handled-badge); font-size: 0.6875rem; padding: 1px 6px; }
  .nested-finding .finding-title { font-size: 0.8125rem; }
  .nested-finding .finding-file { font-size: 0.75rem; }
  .nested-finding-body { display: none; padding: 0 14px 12px 40px; }
  .nested-finding.open .nested-finding-body { display: block; }
  .nested-finding.open > .nested-finding-header > .finding-chevron { transform: rotate(90deg); }
  .nested-finding .resolved-status { color: var(--text-muted); font-style: italic; font-size: 0.8125rem; }
  .handled-reviewer { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
</style>'''

JS = '''<script>
function getPreferredTheme() {
  var stored = localStorage.getItem('pr-respond-theme');
  if (stored) return stored;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('pr-respond-theme', theme);
}
function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}
applyTheme(getPreferredTheme());
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
  if (!localStorage.getItem('pr-respond-theme')) applyTheme(e.matches ? 'dark' : 'light');
});
function toggle(el) { el.classList.toggle('open'); }
function expandAll() { document.querySelectorAll('.finding').forEach(function(f) { f.classList.add('open'); }); }
function collapseAll() { document.querySelectorAll('.finding').forEach(function(f) { f.classList.remove('open'); }); }
</script>'''


def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <respond.md> [output.html]')
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f'Error: {input_path} not found')
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    feedback_lookup = load_feedback_sidecar(input_path)
    html = build_html(fm, sections, feedback_lookup=feedback_lookup)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.html')

    output_path.write_text(html, encoding='utf-8')
    print(output_path)


if __name__ == '__main__':
    main()
