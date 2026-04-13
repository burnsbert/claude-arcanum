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


def parse_pr_target(raw_target):
	target = (raw_target or "").strip()
	if not target:
		return {"kind": "auto-detect"}

	match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", target)
	if match:
		owner, repo, number = match.groups()
		return {
			"kind": "github-pr",
			"owner": owner,
			"repo": repo,
			"repo_full_name": f"{owner}/{repo}",
			"number": int(number),
			"raw": target,
		}

	if re.fullmatch(r"\d+", target):
		return {"kind": "github-pr", "number": int(target), "raw": target}

	return {"kind": "branch-diff", "base_branch": target, "raw": target}


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


def detect_base_branch(repo_path):
	ok, out, _ = maybe_run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo_path)
	if ok and out:
		return out.rsplit("/", 1)[-1]

	ok, out, _ = maybe_run(["git", "remote", "show", "origin"], cwd=repo_path)
	if ok:
		for line in out.splitlines():
			if "HEAD branch:" in line:
				return line.split("HEAD branch:", 1)[1].strip()

	for candidate in ["main", "master", "develop", "development"]:
		ok, _, _ = maybe_run(["git", "rev-parse", "--verify", f"origin/{candidate}"], cwd=repo_path)
		if ok:
			return candidate
	return None


def git_changed_files(repo_path, base_branch):
	ok, out, _ = maybe_run(["git", "diff", "--name-only", f"{base_branch}...HEAD"], cwd=repo_path)
	if not ok:
		return []
	return [line for line in out.splitlines() if line]


def git_commit_list(repo_path, base_branch):
	ok, out, _ = maybe_run(["git", "log", "--oneline", f"{base_branch}...HEAD"], cwd=repo_path)
	if not ok:
		return []
	return [line for line in out.splitlines() if line]


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
			threads.append({
				"isResolved": node.get("isResolved", False),
				"path": node.get("path", ""),
				"line": node.get("line"),
				"comments": comments,
			})
		return threads
	except (json.JSONDecodeError, AttributeError):
		return []


def github_pr_context(parsed):
	repo_full_name = parsed.get("repo_full_name")
	current = cwd_repo_info()
	if not repo_full_name and current and current.get("repo_full_name"):
		repo_full_name = current["repo_full_name"]

	# Phase 1: fetch metadata (needed to resolve owner/repo for parallel calls)
	command = ["gh", "pr", "view", str(parsed["number"]), "--json", "number,title,body,baseRefName,headRefName,headRepositoryOwner,files,additions,deletions,author,state,url,commits"]
	if repo_full_name:
		command.extend(["--repo", repo_full_name])
	metadata = json.loads(run(command).stdout)

	owner = parsed.get("owner") or metadata.get("headRepositoryOwner", {}).get("login") or (repo_full_name.split("/", 1)[0] if repo_full_name else None)
	repo = parsed.get("repo") or (repo_full_name.split("/", 1)[1] if repo_full_name else current.get("repo") if current else None)
	repo_full_name = f"{owner}/{repo}" if owner and repo else repo_full_name

	# Phase 2: fetch diff, review threads, and local repo in parallel
	with ThreadPoolExecutor(max_workers=3) as pool:
		diff_future = pool.submit(fetch_pr_diff, parsed["number"], repo_full_name)
		threads_future = pool.submit(fetch_review_threads, owner, repo, parsed["number"]) if owner and repo else None
		local_future = pool.submit(find_local_repo, owner, repo) if repo else None

		diff_content = diff_future.result()
		review_threads = threads_future.result() if threads_future else []
		local_repo_path = local_future.result() if local_future else None

	# Enrich commits and files from metadata
	commits = []
	for c in metadata.get("commits", []):
		msg = c.get("messageHeadline", "") or c.get("oid", "")
		body = c.get("messageBody", "")
		commits.append({"headline": msg, "body": body})

	files = []
	for f in metadata.get("files", []):
		files.append({
			"path": f.get("path", ""),
			"additions": f.get("additions", 0),
			"deletions": f.get("deletions", 0),
		})

	return {
		"mode": "github-pr",
		"input": parsed,
		"repository": {
			"owner": owner,
			"repo": repo,
			"repo_full_name": repo_full_name,
			"local_path": local_repo_path,
		},
		"pull_request": {
			"number": metadata["number"],
			"title": metadata.get("title", ""),
			"body": metadata.get("body", ""),
			"url": metadata.get("url", ""),
			"state": metadata.get("state", ""),
			"base_branch": metadata.get("baseRefName", ""),
			"head_branch": metadata.get("headRefName", ""),
			"author": metadata.get("author", {}).get("login"),
			"additions": metadata.get("additions"),
			"deletions": metadata.get("deletions"),
			"files_changed": len(files),
			"files": files,
			"commits": commits,
			"commit_count": len(commits),
		},
		"diff": diff_content,
		"review_threads": review_threads,
		"local_checkout": {
			"tracked_dirty": tracked_dirty(local_repo_path) if local_repo_path else None,
			"checkout_branch": metadata.get("headRefName", ""),
		},
	}


def branch_diff_context(parsed):
	current = cwd_repo_info()
	if not current:
		raise RuntimeError("branch-diff mode requires a local git repository")

	repo_path = current["path"]
	base_branch = parsed.get("base_branch") or detect_base_branch(repo_path)
	if not base_branch:
		raise RuntimeError("could not determine a base branch")

	current_branch = run(["git", "branch", "--show-current"], cwd=repo_path).stdout.strip()

	# Fetch diff, stat, and file list in parallel
	with ThreadPoolExecutor(max_workers=3) as pool:
		diff_f = pool.submit(maybe_run, ["git", "diff", f"{base_branch}...HEAD"], repo_path)
		stat_f = pool.submit(maybe_run, ["git", "diff", "--stat", f"{base_branch}...HEAD"], repo_path)
		files_f = pool.submit(maybe_run, ["git", "diff", "--name-only", f"{base_branch}...HEAD"], repo_path)

		diff_ok, diff_out, _ = diff_f.result()
		stat_ok, stat_out, _ = stat_f.result()
		files_ok, files_out, _ = files_f.result()

	return {
		"mode": "branch-diff",
		"input": parsed,
		"repository": current,
		"branch_diff": {
			"base_branch": base_branch,
			"current_branch": current_branch,
			"files_changed": [f for f in files_out.splitlines() if f] if files_ok else [],
			"commit_list": git_commit_list(repo_path, base_branch),
		},
		"diff": diff_out if diff_ok else None,
		"diff_stat": stat_out if stat_ok else None,
		"local_checkout": {
			"tracked_dirty": tracked_dirty(repo_path),
		},
	}


def auto_detect_context():
	current = cwd_repo_info()
	if current:
		ok, out, _ = maybe_run(["gh", "pr", "view", "--json", "number,title,baseRefName,url"], cwd=current["path"])
		if ok and out:
			metadata = json.loads(out)
			parsed = {
				"kind": "github-pr",
				"number": metadata["number"],
				"owner": current.get("owner"),
				"repo": current.get("repo"),
				"repo_full_name": current.get("repo_full_name"),
				"raw": "",
			}
			return github_pr_context(parsed)
	return branch_diff_context({"kind": "branch-diff", "base_branch": None, "raw": ""})


def main():
	raw_target = sys.argv[1] if len(sys.argv) > 1 else ""
	try:
		parsed = parse_pr_target(raw_target)
		if parsed["kind"] == "auto-detect":
			payload = auto_detect_context()
		elif parsed["kind"] == "github-pr":
			payload = github_pr_context(parsed)
		else:
			payload = branch_diff_context(parsed)

		payload["environment"] = {
			"cwd": os.getcwd(),
		}
		print(json.dumps(payload, indent=2, sort_keys=True))
	except Exception as exc:
		print(json.dumps({"error": str(exc), "input": raw_target}, indent=2))
		sys.exit(1)


if __name__ == "__main__":
	main()
