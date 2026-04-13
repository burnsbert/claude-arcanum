#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run(command, cwd=None, check=True):
	result = subprocess.run(
		command,
		cwd=cwd,
		text=True,
		capture_output=True,
	)
	if check and result.returncode != 0:
		raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "command failed")
	return result


def maybe_run(command, cwd=None):
	result = subprocess.run(
		command,
		cwd=cwd,
		text=True,
		capture_output=True,
	)
	return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def parse_args(argv):
	"""Parse CLI args, extracting flags before passing the rest to parse_target."""
	reviewers_filter = []
	rest = []

	for arg in argv:
		if arg.startswith("--reviewers="):
			reviewers_filter.extend(arg.split("=", 1)[1].split(","))
		elif arg == "--reviewers" and rest:
			# Handle --reviewers name,name (space-separated)
			pass  # Will be handled in next iteration
		else:
			rest.append(arg)

	# Handle --reviewers as a separate token followed by value
	cleaned = []
	skip_next = False
	for i, arg in enumerate(rest):
		if skip_next:
			skip_next = False
			continue
		if arg == "--reviewers" and i + 1 < len(rest):
			reviewers_filter.extend(rest[i + 1].split(","))
			skip_next = True
		else:
			cleaned.append(arg)

	return cleaned, reviewers_filter


def parse_target(argv):
	if not argv:
		raise RuntimeError("usage: fetch-feedback.py [--reviewers=name,name] <PR-URL | PR-number> [humans | reviewer-names...]")

	target = argv[0].strip()
	match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", target)
	if match:
		owner, repo, number = match.groups()
		return {
			"owner": owner,
			"repo": repo,
			"repo_full_name": f"{owner}/{repo}",
			"number": int(number),
			"filters": argv[1:],
		}

	if re.fullmatch(r"\d+", target):
		view = json.loads(run(["gh", "pr", "view", target, "--json", "number,title,url,headRepositoryOwner,headRefName,baseRefName"]).stdout)
		repo_view = run(["gh", "repo", "view", "--json", "nameWithOwner"]).stdout
		repo_full_name = json.loads(repo_view)["nameWithOwner"]
		owner, repo = repo_full_name.split("/", 1)
		return {
			"owner": owner,
			"repo": repo,
			"repo_full_name": repo_full_name,
			"number": int(view["number"]),
			"filters": argv[1:],
		}

	raise RuntimeError("target must be a GitHub PR URL or PR number")


def reviewer_display_name(author_dict):
	"""Compute display name: 'Brian Smith' -> 'Brian S.', single name or missing -> username."""
	if not isinstance(author_dict, dict):
		return None
	full_name = author_dict.get("name") or ""
	login = author_dict.get("login") or ""
	if full_name:
		parts = full_name.strip().split()
		if len(parts) >= 2:
			return f"{parts[0]} {parts[-1][0]}."
		if parts:
			return parts[0]
	return login or None


def reviewer_name(author):
	if not isinstance(author, dict):
		return None
	return author.get("login") or author.get("name")


def is_bot_name(name):
	if not name:
		return False
	lower_name = name.lower()
	return (
		lower_name.endswith("[bot]")
		or lower_name.endswith("-bot")
		or "coderabbit" in lower_name
		or "github-actions" in lower_name
		or "dependabot" in lower_name
		or "renovate" in lower_name
	)


def is_bot_meta_comment(item):
	"""Filter out non-informative bot comments (summaries, walkthroughs, etc.)."""
	if not item.get("is_bot"):
		return False
	# Only filter comments without a specific file/line (not inline review feedback)
	if item.get("file"):
		return False
	body = (item.get("body") or "").strip()
	# CodeRabbit review summary ("Actionable comments posted: N")
	if re.match(r"^\*?\*?Actionable comments posted:", body):
		return True
	# CodeRabbit walkthrough / auto-generated summary
	if "<!-- This is an auto-generated comment" in body:
		return True
	if body.startswith("<!-- walkthrough"):
		return True
	return False


def include_item(item, filters):
	# Always drop non-informative bot meta-comments
	if is_bot_meta_comment(item):
		return False

	if not filters:
		return True

	reviewer = (item.get("reviewer") or "").lower()
	display = (item.get("reviewer_display") or "").lower()

	if len(filters) == 1 and filters[0].lower() == "humans":
		return not item.get("is_bot", False)

	needles = {token.lower() for token in filters}
	return reviewer in needles or display in needles


def normalize_review(review):
	author = review.get("author", {})
	name = reviewer_name(author)
	return {
		"source": "review",
		"reviewer": name,
		"reviewer_display": reviewer_display_name(author) or name,
		"is_bot": is_bot_name(name),
		"body": review.get("body") or "",
		"state": review.get("state"),
		"file": None,
		"line": None,
		"comment_id": None,
		"review_id": review.get("id"),
		"url": review.get("url"),
		"created_at": review.get("submittedAt") or review.get("createdAt"),
	}


def normalize_pr_comment(comment):
	user = comment.get("user", {})
	name = reviewer_name(user)
	line = comment.get("line") or comment.get("original_line")
	start_line = comment.get("start_line") or comment.get("original_start_line")
	return {
		"source": "pull_request_comment",
		"reviewer": name,
		"reviewer_display": reviewer_display_name(user) or user.get("login") or name,
		"is_bot": is_bot_name(user.get("login") or name),
		"body": comment.get("body") or "",
		"state": None,
		"file": comment.get("path"),
		"line": line,
		"start_line": start_line if start_line and start_line != line else None,
		"comment_id": comment.get("id"),
		"review_id": comment.get("pull_request_review_id"),
		"url": comment.get("html_url") or comment.get("url"),
		"created_at": comment.get("created_at") or comment.get("updated_at"),
	}


def normalize_issue_comment(comment):
	user = comment.get("user", {})
	name = reviewer_name(user)
	return {
		"source": "issue_comment",
		"reviewer": name,
		"reviewer_display": reviewer_display_name(user) or user.get("login") or name,
		"is_bot": is_bot_name(user.get("login") or name),
		"body": comment.get("body") or "",
		"state": None,
		"file": None,
		"line": None,
		"comment_id": comment.get("id"),
		"review_id": None,
		"url": comment.get("html_url") or comment.get("url"),
		"created_at": comment.get("created_at") or comment.get("updated_at"),
	}


def fetch_pr_diff(number, repo_full_name):
	"""Fetch the full unified diff for a PR."""
	command = ["gh", "pr", "diff", str(number)]
	if repo_full_name:
		command.extend(["--repo", repo_full_name])
	ok, out, _ = maybe_run(command)
	return out if ok else None


def fetch_review_threads(owner, repo, number):
	"""Fetch review threads with resolution status via GraphQL."""
	query = '''query {
  repository(owner: "%s", name: "%s") {
    pullRequest(number: %d) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          path
          line
          startLine
          comments(first: 10) {
            nodes {
              body
              author { login }
            }
          }
        }
      }
    }
  }
}''' % (owner, repo, number)
	ok, out, _ = maybe_run(["gh", "api", "graphql", "-f", f"query={query}"])
	if not ok or not out:
		return []
	try:
		data = json.loads(out)
		nodes = data.get("data", {}).get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])
		threads = []
		for node in nodes:
			comments = []
			for c in node.get("comments", {}).get("nodes", []):
				comments.append({
					"author": c.get("author", {}).get("login", "unknown"),
					"body": c.get("body", ""),
				})
			line = node.get("line")
			start_line = node.get("startLine")
			threads.append({
				"isResolved": node.get("isResolved", False),
				"path": node.get("path", ""),
				"line": line,
				"start_line": start_line if start_line and start_line != line else None,
				"comments": comments,
			})
		return threads
	except (json.JSONDecodeError, AttributeError):
		return []


def parse_remote_url(remote_url):
	remote_url = remote_url.strip()
	match = re.match(r"git@github\.com:([^/]+)/([^/.]+)(?:\.git)?$", remote_url)
	if match:
		return match.group(1), match.group(2)
	match = re.match(r"https://github\.com/([^/]+)/([^/.]+)(?:\.git)?$", remote_url)
	if match:
		return match.group(1), match.group(2)
	return None, None


def cwd_repo_info():
	cwd = Path.cwd()
	ok, _, _ = maybe_run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
	if not ok:
		return None

	root = run(["git", "rev-parse", "--show-toplevel"], cwd=cwd).stdout.strip()
	remote_ok, remote_out, _ = maybe_run(["git", "remote", "get-url", "origin"], cwd=root)
	owner = None
	repo = None
	if remote_ok and remote_out:
		owner, repo = parse_remote_url(remote_out)
	return {
		"path": root,
		"owner": owner,
		"repo": repo,
		"repo_full_name": f"{owner}/{repo}" if owner and repo else None,
		"remote_url": remote_out if remote_ok else None,
	}


def find_local_repo(owner, repo):
	candidates = []
	current = cwd_repo_info()
	if current and current.get("repo") == repo and (not owner or current.get("owner") == owner):
		candidates.append(Path(current["path"]))

	home = Path.home()
	candidates.extend([
		home / "src" / repo,
		home / "src" / owner / repo if owner else None,
	])

	seen = set()
	for candidate in candidates:
		if candidate is None:
			continue
		candidate = candidate.expanduser()
		key = str(candidate)
		if key in seen:
			continue
		seen.add(key)
		if not candidate.exists():
			continue
		ok, _, _ = maybe_run(["git", "rev-parse", "--show-toplevel"], cwd=candidate)
		if ok:
			return str(candidate.resolve())
	return current["path"] if current and current.get("repo") == repo else None


def tracked_dirty(repo_path):
	ok, out, _ = maybe_run(["git", "status", "--porcelain"], cwd=repo_path)
	if not ok:
		return None
	return any(line and not line.startswith("??") for line in out.splitlines())


def main():
	try:
		cleaned_args, reviewers_filter = parse_args(sys.argv[1:])
		target = parse_target(cleaned_args)
		repo_full_name = target["repo_full_name"]
		owner = target["owner"]
		repo = target["repo"]
		number = target["number"]
		number_str = str(number)

		# Merge --reviewers flag with positional filters
		filters = target["filters"]
		if reviewers_filter:
			filters = filters + reviewers_filter

		# Phase 1: fetch metadata (needed to resolve owner/repo/branches)
		pr_view = json.loads(run(["gh", "pr", "view", number_str, "--repo", repo_full_name,
			"--json", "title,body,baseRefName,headRefName,url,reviews,comments,commits,files,additions,deletions,author,state"]).stdout)

		# Phase 2: parallel fetches for diff, review threads, inline comments, issue comments, local repo
		with ThreadPoolExecutor(max_workers=5) as pool:
			diff_future = pool.submit(fetch_pr_diff, number, repo_full_name)
			threads_future = pool.submit(fetch_review_threads, owner, repo, number) if owner and repo else None
			inline_future = pool.submit(lambda: json.loads(run(["gh", "api", f"repos/{repo_full_name}/pulls/{number_str}/comments"]).stdout))
			issue_future = pool.submit(lambda: json.loads(run(["gh", "api", f"repos/{repo_full_name}/issues/{number_str}/comments"]).stdout))
			local_future = pool.submit(find_local_repo, owner, repo) if repo else None

			diff_content = diff_future.result()
			review_threads = threads_future.result() if threads_future else []
			inline_comments = inline_future.result()
			issue_comments = issue_future.result()
			local_repo_path = local_future.result() if local_future else None

		# Normalize feedback items
		items = []
		for review in pr_view.get("reviews", []):
			normalized = normalize_review(review)
			if normalized["body"].strip():
				items.append(normalized)

		for comment in inline_comments:
			items.append(normalize_pr_comment(comment))

		for comment in issue_comments:
			items.append(normalize_issue_comment(comment))

		filtered_items = [item for item in items if include_item(item, filters)]
		filtered_items.sort(key=lambda item: ((item.get("reviewer") or "").lower(), item.get("created_at") or "", item.get("comment_id") or 0))

		reviewer_counts = {}
		source_counts = {}
		for item in filtered_items:
			reviewer_counts[item.get("reviewer") or "unknown"] = reviewer_counts.get(item.get("reviewer") or "unknown", 0) + 1
			source_counts[item["source"]] = source_counts.get(item["source"], 0) + 1

		# Enrich commits
		commits = []
		for c in pr_view.get("commits", []):
			msg = c.get("messageHeadline", "") or c.get("oid", "")
			body = c.get("messageBody", "")
			commits.append({"headline": msg, "body": body})

		# Enrich file stats
		file_stats = []
		for f in pr_view.get("files", []):
			file_stats.append({
				"path": f.get("path", ""),
				"additions": f.get("additions", 0),
				"deletions": f.get("deletions", 0),
			})

		payload = {
			"pull_request": {
				"number": number,
				"repo_full_name": repo_full_name,
				"title": pr_view.get("title", ""),
				"body": pr_view.get("body", ""),
				"base_branch": pr_view.get("baseRefName", ""),
				"head_branch": pr_view.get("headRefName", ""),
				"url": pr_view.get("url", ""),
				"state": pr_view.get("state", ""),
				"author": pr_view.get("author", {}).get("login"),
				"additions": pr_view.get("additions"),
				"deletions": pr_view.get("deletions"),
				"files_changed": len(file_stats),
				"files": file_stats,
				"commits": commits,
				"commit_count": len(commits),
			},
			"filters": filters,
			"counts": {
				"total_items": len(filtered_items),
				"reviewers": reviewer_counts,
				"sources": source_counts,
			},
			"items": filtered_items,
			"diff": diff_content,
			"review_threads": review_threads,
			"local_repo_path": local_repo_path,
			"local_checkout": {
				"tracked_dirty": tracked_dirty(local_repo_path) if local_repo_path else None,
				"checkout_branch": pr_view.get("headRefName", ""),
			},
			"environment": {
				"cwd": os.getcwd(),
			},
		}
		print(json.dumps(payload, indent=2, sort_keys=True))
	except Exception as exc:
		print(json.dumps({"error": str(exc)}, indent=2))
		sys.exit(1)


if __name__ == "__main__":
	main()
