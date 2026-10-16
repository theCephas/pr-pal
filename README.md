# PR Pal

A free, private AI reviewer that checks your pull request before you submit it.
It runs an open-weight model locally via Ollama, flags low-effort or spam-like
changes, checks the repo's CONTRIBUTING.md, and drafts your PR description.

Built for Hacktoberfest 2026 (Best Open-Source AI Project).

## Why
Every October, maintainers get flooded with low-quality pull requests.
PR Pal helps contributors catch problems before a maintainer has to.

## Open-weight AI
The review is done by an open-weight model running on your own machine
through Ollama. Default: `qwen2.5-coder:1.5b`. Change it with
`export PR_PAL_MODEL=llama3.2:3b`. No code is sent to a paid API.

## Agent Skill
`skills/pr-pal/` is a self-contained skill following the Agent Skill Open
Standard: `SKILL.md` plus `scripts/pr_pal.py`. Any compatible agent can load it.

## Setup
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5-coder:1.5b
```
No Python packages needed.

## Use
From inside any git repo, on your feature branch:
```bash
python skills/pr-pal/scripts/pr_pal.py --base main
```
Add `--json` for a machine-readable report. Exit code is 0 when ready,
1 when it needs work.

## License
MIT
