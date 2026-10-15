# custom_maintenance - maintenance kit for the "all features unlocked" OpenProject fork

| File | Audience | Content |
|------|----------|---------|
| [HUMAN_GUIDE.md](HUMAN_GUIDE.md) | people | release workflow, per-release checklist, tooling (Git, IDEs, diff/merge tools), custom scripts, smoke test |
| [CUSTOMIZATIONS_REGISTRY.md](CUSTOMIZATIONS_REGISTRY.md) | both | every deliberate difference from upstream (EE removals per feature, local fixes, fork-only features), open findings |
| [AGENT_PLAYBOOK.md](AGENT_PLAYBOOK.md) | AI agents | rules, step-by-step procedure, removal recipes per restriction pattern, how to learn/record new patterns |
| `restriction_patterns.tsv` | tooling | catalog of ways EE restrictions are implemented (regex + recipe) |
| `invariants.tsv` | tooling | assertions that our customizations are still in place |
| `known_residuals.tsv` | tooling | triaged baseline of residual EE references (unused infrastructure) |
| `../custom_scripts/enterprise_audit.py` | tooling | `scan`, `verify`, `upstream-impact`, `delta-diff`, `markers` |
| `../.claude/skills/openproject-ee-unlock-maintenance/SKILL.md` | Claude Code | auto-discovered entry point for new sessions |

Quick start after merging a new upstream tag:

```bash
python3 custom_scripts/enterprise_audit.py verify      # are our customizations intact?  (must be 100%)
python3 custom_scripts/enterprise_audit.py scan        # any new Enterprise restriction? (must be 0 NEW)
```

Baseline of this kit: fork at **v17.9.1** - 64 invariants, 151 baselined residual hits, 19 pattern families.
