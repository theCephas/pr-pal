---
name: pr-pal
description: Reviews a git pull request locally before it is opened. Checks the diff against the target repo's CONTRIBUTING.md, flags low-effort or spam-like changes, and drafts a PR title and description using an open-weight model via Ollama. Use when the user is about to open a pull request, asks if their PR is ready, or mentions Hacktoberfest contributions.
license: MIT
compatibility: Requires git, Python 3.10+, and Ollama running locally with an open-weight model pulled (default qwen2.5-coder:1.5b).
metadata:
  author: pr-pal-contributors
  version: "1.0.0"
---

# PR Pal

## When to use
Use before the user opens a pull request, or when they ask whether a change is ready to submit.

## Steps
1. Confirm you are inside a git repository with committed changes on a feature branch.
2. Run `python scripts/pr_pal.py --base <base-branch> --json` (default base is `main`).
3. Read the JSON report. Show the user the verdict first, then each issue with its fix.
4. If the verdict is `ready`, offer the drafted PR title and description.
5. If the verdict is `needs-work`, help fix the listed issues, then run the review again.

## Judging quality
- Low-effort: only whitespace, a typo fix in an unrelated README, adding a name to a list, renaming with no reason.
- Spam signs: the same change copied across many files, generated text with no linked issue, unexplained deletions.
- Good: links an issue, includes tests or docs, follows the repo's style and commit rules.

## Do not
- Do not open the PR yourself unless the user asks.
- Do not send code to any remote API; the model runs locally.
