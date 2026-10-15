# repo-maintenance

A Hermes Agent Skill for repository maintenance analysis.

## Description

This skill inspects a Git repository and identifies maintenance problems
related to dependencies, Python version compatibility, and code quality.

## Usage

```
hermes skills opt-in --sync
```

Then use:

```
/repo-maintenance inspect <path>
/repo-maintenance analyze <path>
```

## Configuration

Requires Hermes Agent with an configured open-weight AI model.

## Options

| Option | Description |
|--------|-------------|
| `inspect <path>` | Inspect a repository and display metadata |
| `analyze <path>` | Analyze a repository for maintenance issues |
| `analyze-with-ai <path>` | Analyze using Hermes Agent AI |

## See Also

- https://agentskills.io/home
- Hermes Agent documentation: https://hermes-agent.nousresearch.com/docs