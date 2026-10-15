# RepoRescue-AI Demo Script

**Duration:** 5–7 minutes  
**Audience:** Hackathon judges  
**Repo:** https://github.com/rishrek/LinkWatch (local clone)

---

## 1. INPUT — "What repo should I check?"

```powershell
# Show the target repo
ls C:\Users\Yash\Desktop\LinkWatch

# Run inspection only (fast, no AI needed)
re-rescue inspect C:\Users\Yash\Desktop\LinkWatch
```

**Show output:**
- Git repo detected (commit hash, branch)
- Manifests found: `pyproject.toml`, `requirements.txt`
- 15 Python source files, 4 test files
- Dependencies listed with versions

**Talking point:** *"One command, any repo. No hardcoded paths."*

---

## 2. ANALYSIS — "What's wrong?"

```powershell
# Full analysis (static findings + AI if Hermes configured)
re-rescue analyze C:\Users\Yash\Desktop\LinkWatch
```

**Show output (terminal):**
- Findings table printed to console
- Each finding: category, severity, evidence
- Capsule file generated: `Dependency_Exit_Capsule_<timestamp>.md`

**Talking point:** *"Evidence-based findings, not guesses. Every row has a source file and line."*

---

## 3. EVIDENCE — "Prove it."

```powershell
# Open the capsule
notepad Dependency_Exit_Capsule_*.md
```

**Scroll through and highlight:**
- **Repository Metadata** — commit, branch, type
- **Dependency Manifests** — parsed content
- **Findings** — each with `Evidence:` field pointing to exact file/line
- **AI Hypotheses** — clearly labeled `HYPOTHESIS:` vs `VERIFIED:`
- **Proposed Actions** — specific commands to run
- **Verification Steps** — how to confirm fix works

**Talking point:** *"Capsule is reproducible — same input = same output. Auditable."*

---

## 4. VERIFICATION — "Does the fix work?"

```powershell
# Example: verify pydantic pinning fix
cd C:\Users\Yash\Desktop\LinkWatch

# Show current state
grep pydantic pyproject.toml

# Proposed action from capsule: pin to pydantic>=2,<3
# Run tests to verify compatibility
python -m pytest tests/ -v
```

**Show test results pass.**

**Talking point:** *"Every proposed action includes a verification step. No blind fixes."*

---

## 5. OUTPUT — "What do I get?"

**Artifacts produced:**
1. **Console summary** — quick findings table
2. **Dependency Exit Capsule (Markdown)** — full evidence, hypotheses, actions, verification
3. **Machine-readable JSON** — (if `--json` flag added) for CI integration

**Show capsule structure:**
```
## Repository Metadata
## Dependency Manifests
## Findings (with Evidence)
## AI Hypotheses (labeled)
## Proposed Maintenance Actions
## Verification Steps
## Commands Executed & Results
## Compatibility Gaps & Limitations
```

**Talking point:** *"One file tells the whole story — hand it to a maintainer, they know exactly what to do."*

---

## 6. ERROR HANDLING — "What if things break?"

```powershell
# Non-existent path
re-rescue analyze C:\fake\path
# → Clear error: "Not a valid repository"

# Malformed pyproject.toml
# (create temp dir with broken TOML)
mkdir C:\temp\broken
echo "invalid toml [" > C:\temp\broken\pyproject.toml
re-rescue analyze C:\temp\broken
# → Graceful error: "Failed to parse pyproject.toml"

# Missing git
mkdir C:\temp\nogit
echo "print('hi')" > C:\temp\nogit\main.py
re-rescue analyze C:\temp\nogit
# → Works (non-git dir), warns "Not a git repository"
```

**Talking point:** *"Fails fast, tells you why, never crashes silently."*

---

## Backup Slides (If Asked)

| Question | Answer |
|----------|--------|
| "How does AI fit in?" | Hermes Agent calls local open-weight model; hypotheses labeled until verified |
| "Why not just use pip-audit?" | We find *maintenance* issues (unpinned deps, version gaps), not just CVEs |
| "Can it fix things?" | Proposes actions + verification steps; human approves before any change |
| "What models work?" | Any tool-calling model via Hermes: Llama 3.2 1B, Phi-3 3.8B, Gemma 2B (local) |
| "Is it LinkWatch-specific?" | No — tested on LinkWatch, works on any Python/JS/Go repo with manifests |

---

## Timing Cheat Sheet

| Segment | Time |
|---------|------|
| Input (inspect) | 1 min |
| Analysis (analyze) | 1–2 min |
| Evidence (capsule walkthrough) | 2 min |
| Verification (live test run) | 1 min |
| Output (capsule artifacts) | 30 sec |
| Error handling demo | 1 min |
| **Total** | **~6–7 min** |

---

## One-Liner for Judges

> *"RepoRescue-AI turns 'I wonder if this repo has problems' into a verified, auditable maintenance plan — in one command."*