---
name: openproject-ee-unlock-maintenance
description: Maintain the internal OpenProject fork where all Enterprise features are unlocked. Use when integrating a new upstream OpenProject release/tag, merging upstream, hunting or removing Enterprise (EE) restrictions/banners/upsell/token checks/user limits, reviewing merge results against our customizations, or when the user mentions "enterprise restriction", "code-maintenance", "changes from vX.Y.Z", "sync_upstream" or "custom_maintenance".
---

# OpenProject EE-unlock fork maintenance

This repository is an internal fork of OpenProject in which every Community and Enterprise feature works without a
license token. The Enterprise token model is untouched; each restriction call site was edited by hand, so every
new upstream token check silently re-introduces a restriction.

Do this, in order:

1. Read `custom_maintenance/AGENT_PLAYBOOK.md` completely (rules, procedure, recipes R1-R9, how to record new knowledge).
2. Read `custom_maintenance/CUSTOMIZATIONS_REGISTRY.md` (what differs from upstream and where; open findings F-*).
3. Use the tooling (Python 3, no dependencies):
   - `python3 custom_scripts/enterprise_audit.py upstream-impact <old_tag> <new_tag>` before merging
   - `custom_scripts/sync_upstream <old_tag> <new_tag>` to merge (leaves the merge uncommitted)
   - `python3 custom_scripts/enterprise_audit.py verify` (must pass) and `scan` (no NEW hits)
   - `python3 custom_scripts/enterprise_audit.py delta-diff <old_tag> <new_tag>` to review what changed in our delta
4. Keep changes surgical; never fake a token; never revert a customization while resolving conflicts; do not commit,
   push or tag without the user's request.
5. Before finishing, update the knowledge base (registry, `invariants.tsv`, `restriction_patterns.tsv`,
   `known_residuals.tsv`) and report using the output contract at the end of the playbook.

Human-oriented companion: `custom_maintenance/HUMAN_GUIDE.md`.
