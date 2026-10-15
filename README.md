# RepoRescue-AI

AI-powered repository maintenance agent for Hackathon 2026 — "Building Resilient Open-Source Software with AI".

## Overview

RepoRescue-AI is a reusable AI-powered maintenance agent that can:
- **Inspect** arbitrary Git repositories (dependency manifests, source files, config, tests)
- **Identify** evidence-supported maintenance problems (version conflicts, unpinned deps, compatibility gaps)
- **Analyze** findings via an open-weight AI model through Hermes Agent
- **Verify** results using real tools (pytest, pip, git)
- **Generate** a **Dependency Exit Capsule** (Markdown) with evidence, hypotheses, actions, and verification steps

The tool works on **any compatible repository** — no hardcoded paths, findings, or outputs.  
Mandatory demo target: https://github.com/rishrek/LinkWatch

## Features

| Feature | Status |
|---------|--------|
| Dynamic repository inspection (git, manifests, source, tests) | ✅ Working |
| Evidence-based finding detection (Python version, deps, coverage) | ✅ Working |
| AI analysis via Hermes Agent (open-weight models) | ⚠️ Requires Hermes + model |
| Automated test execution & verification | ✅ Designed |
| Dependency Exit Capsule generation (Markdown) | ✅ Working |
| Verified facts vs. AI hypotheses separation | ✅ Architected |
| Arbitrary repository support | ✅ Designed, LinkWatch tested |

## Quick Start (No Hermes Required for Core Demo)

```powershell
# 1. Clone & install
git clone <your-fork-url> RepoRescue-AI
cd RepoRescue-AI
pip install -e .

# 2. Run static analysis (no AI) — generates capsule with detected findings
re-rescue analyze C:\path\to\LinkWatch

# 3. View the Dependency Exit Capsule
notepad Dependency_Exit_Capsule_*.md
```

**With Hermes + local model** (for full AI analysis):
```powershell
# Install Hermes (one-time)
iex (irm https://hermes-agent.nousresearch.com/install.ps1)

# Configure local model (LM Studio / Ollama)
hermes model  # → Custom Endpoint → http://127.0.0.1:1234/v1

# Run full AI-powered analysis
re-rescue analyze C:\path\to\LinkWatch
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  CLI (re-rescue) │────▶│  Inspection      │────▶│  Analysis Engine   │
│  inspect/analyze │     │  (manifests,     │     │  (findings +       │
└─────────────────┘     │   source, tests) │     │   AI hypotheses)   │
                        └──────────────────┘     └─────────┬──────────┘
                                                           │
                        ┌──────────────────┐               │
                        │  Hermes Agent    │◀──────────────┘
                        │  (AI analysis)   │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Exit Capsule    │
                        │  (Markdown)      │
                        └──────────────────┘
```

### Core Modules
| Module | Purpose |
|--------|---------|
| `src/reporescue/inspection.py` | Git repo detection, manifest parsing, file discovery |
| `src/reporescue/analysis.py` | Finding detection, evidence collection, AI prompt building |
| `src/reporescue/cli.py` | CLI commands, capsule generation |
| `skills/repo-maintenance/SKILL.md` | Hermes Agent Skill (Agent Skills Open Standard) |

## LinkWatch Analysis (Demo Results)

Running `re-rescue analyze` on LinkWatch produces:

| Finding | Category | Severity | Evidence |
|---------|----------|----------|----------|
| Python 3.10+ required | python-version | info | `requires-python = ">=3.10"` ✅ compliant |
| `chardet==5.2.0` pinned | dependency-version | info | `requirements.txt` / `pyproject.toml` |
| `pydantic>=2` unpinned | dependency-version | warning | Risk of v1/v2 API breakage |
| 15 Python source files | dependency-analysis | info | `linkwatch/*.py` |
| 4 test files | dependency-analysis | info | `tests/test_*.py` |

> **Note:** LinkWatch's `pyproject.toml` already specifies `>=3.10` (hackathon-compliant). The earlier summary incorrectly reported `>=3.14`.

## AI Model Configuration (Hermes)

RepoRescue-AI requires an **open-weight model** via Hermes Agent.

### Recommended: Local Inference (Fully Compliant)
| Option | Setup |
|--------|-------|
| **LM Studio** (GUI) | 1. Install from lmstudio.ai 2. Download Llama 3.2 1B / Phi-3 3.8B 3. Start server (Developer tab) 4. Hermes: Custom Endpoint → `http://127.0.0.1:1234/v1` |
| **Ollama** (CLI) | `ollama pull llama3.2:1b` → `ollama serve` → Hermes: Custom Endpoint → `http://127.0.0.1:11434/v1` |

### Model Requirements
- Supports tool/function calling
- Runs locally (no paid APIs)
- 1B–8B params fits consumer GPU/CPU

## CLI Reference

```powershell
re-rescue inspect <path>     # Inspect only (no AI, fast)
re-rescue analyze <path>     # Full analysis + capsule (needs Hermes)
re-rescue --help             # Show all options
```

## Project Structure

```
RepoRescue-AI/
├── pyproject.toml              # Project config, deps, CLI entry
├── README.md                   # This file
├── LICENSE                     # MIT
├── skills/
│   └── repo-maintenance/
│       └── SKILL.md            # Hermes Agent Skill
├── src/
│   └── reporescue/
│       ├── __init__.py         # v0.1.0
│       ├── inspection.py       # Repo inspection
│       ├── analysis.py         # Finding detection & AI prompts
│       └── cli.py              # CLI + capsule generation
├── tests/
│   └── __init__.py
└── examples/
    └── basic_analysis.py       # Programmatic usage example
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `click` | CLI framework |
| `pyyaml` | Config parsing |
| `tomli` | TOML parsing (pyproject.toml) |
| `packaging` | Version comparison |
| `gitpython` | Git repo inspection |

## Limitations

- **Read-only by default** — never modifies target repository
- **AI hypotheses labeled** — all AI output marked until verified
- **Bounded context** — only relevant files sent to model
- **No auto-fix** — proposes actions, requires human approval
- **Graceful degradation** — works without Hermes (static analysis only)
- **Python 3.12+** — tested on 3.12.10

## License

MIT — see [LICENSE](LICENSE)

## Hackathon Submission Checklist

- [x] Public GitHub repo (fork of starter)
- [x] MIT license
- [x] Complete README (overview, setup, usage, architecture, deps, model, limitations)
- [x] Meaningful Git commits (see `git log --oneline`)
- [x] Dynamic LinkWatch analysis demo
- [x] Reproducible Dependency Exit Capsule
- [x] Hermes Agent Skill (agentskills.io standard)
- [x] Open-weight model support (local)
- [ ] 6-slide Canva presentation
- [ ] Demo script (input → analysis → evidence → verification → output → error handling)