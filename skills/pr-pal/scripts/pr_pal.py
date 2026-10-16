"""PR Pal: review your pull request locally with an open-weight model.

Usage:  python pr_pal.py --base main [--json]
Needs:  git, Python 3.10+, and Ollama running with an open-weight model.
No extra Python packages required.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("PR_PAL_MODEL", "qwen2.5-coder:1.5b")
MAX_DIFF_CHARS = 12000

SYSTEM = """You are PR Pal, a strict but kind open-source maintainer.
Review the pull request diff against the repo's contribution rules.
Respond ONLY with JSON in this exact shape:
{"verdict": "ready" or "needs-work",
 "summary": "one sentence",
 "issues": [{"file": "path", "problem": "text", "fix": "text"}],
 "pr_title": "short title",
 "pr_body": "markdown PR description"}"""


# 1. Collect the evidence from git -------------------------------------------
def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def collect(base):
    mb = git("merge-base", base, "HEAD").strip()
    diff = git("diff", mb, "HEAD")
    files = [f for f in git("diff", "--name-only", mb, "HEAD").splitlines() if f]
    commits = [c for c in git("log", "--format=%s", f"{mb}..HEAD").splitlines() if c]
    rules = ""
    for name in ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md"):
        if Path(name).exists():
            rules = Path(name).read_text(errors="ignore")[:6000]
            break
    return diff, files, commits, rules


# 2. Fast rule checks, no AI -------------------------------------------------
def rule_checks(diff, files, commits):
    added = removed = blank = 0
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("+"):
            added += 1
            blank += not line[1:].strip()
        elif line.startswith("-"):
            removed += 1

    issues = []

    def flag(severity, problem, fix):
        issues.append({"severity": severity, "problem": problem, "fix": fix})

    if added + removed == 0:
        flag("error", "No changes found against the base branch.", "Commit your work first.")
    elif added == blank and removed == 0:
        flag("error", "Only blank lines were added.", "Make a meaningful change.")
    if files and all(f.lower().endswith(".md") for f in files) and added < 5:
        flag("warning", "Tiny docs-only change; maintainers may mark it as spam.",
             "Link it to an open issue or expand it.")
    if removed > 50 and removed > 3 * max(added, 1):
        flag("warning", "Large deletion with little added.", "Explain why in the PR body.")
    for msg in commits:
        if len(msg) < 10:
            flag("warning", f"Vague commit message: '{msg}'.",
                 "Describe what changed, e.g. 'Fix crash when config is empty'.")
    return issues, {"added": added, "removed": removed, "blank_added": blank}


# 3. Ask the local open-weight model -----------------------------------------
def ai_review(diff, rules, rule_issues):
    prompt = (f"CONTRIBUTING.md:\n{rules or '(none found)'}\n\n"
              f"Automatic checks found:\n{json.dumps(rule_issues)}\n\n"
              f"Diff:\n{diff[:MAX_DIFF_CHARS]}")
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "format": "json", "stream": False, "options": {"temperature": 0.2},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        content = json.load(resp)["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"verdict": "needs-work", "summary": "Model reply was not valid JSON.",
                "issues": [], "pr_title": "", "pr_body": content}


# 4. Put it together ---------------------------------------------------------
def main():
    p = argparse.ArgumentParser(prog="pr-pal", description="Review your PR locally.")
    p.add_argument("--base", default="main", help="branch you will merge into")
    p.add_argument("--json", action="store_true", help="print a JSON report")
    args = p.parse_args()

    diff, files, commits, rules = collect(args.base)
    rule_issues, stats = rule_checks(diff, files, commits)
    report = ai_review(diff, rules, rule_issues)
    if any(i["severity"] == "error" for i in rule_issues):
        report["verdict"] = "needs-work"
    report["rule_checks"], report["stats"] = rule_issues, stats

    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"Verdict: {str(report.get('verdict', '?')).upper()}")
    print(report.get("summary", ""))
    for i in rule_issues + report.get("issues", []):
        print(f"- [{i.get('file') or i.get('severity', '')}] {i.get('problem')} -> {i.get('fix')}")
    if report.get("verdict") == "ready":
        print(f"\nSuggested title: {report.get('pr_title')}\n\n{report.get('pr_body')}")
    sys.exit(0 if report.get("verdict") == "ready" else 1)


if __name__ == "__main__":
    main()
