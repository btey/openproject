# Human Guide - Maintaining the Unlocked OpenProject Fork

For the team that integrates each new upstream OpenProject release.
Companion documents: [CUSTOMIZATIONS_REGISTRY.md](CUSTOMIZATIONS_REGISTRY.md) (what we changed and where) and
[AGENT_PLAYBOOK.md](AGENT_PLAYBOOK.md) (the same procedure written for an AI agent).

---

## 1. What this fork is

An internal build of the open-source OpenProject app in which every Community **and** Enterprise feature works
without a license token. We keep the upstream code and make the smallest possible edits to lift restrictions.
On top of that we maintain a few local fixes, a GitLab integration extension, a slim production Dockerfile, a GitLab CI
pipeline and some operational scripts (`custom_scripts/`).

Repository facts that matter for maintenance:

- Remotes: `origin` = internal GitLab (`git.bethelservice.org/cdsupportdevelopers/general/openproject`),
  `upstream` = `https://github.com/opf/openproject.git`.
- Default branch: `develop`. Maintenance branches: `code-maintenance/op-<ticket>-changes-from-v<major>-<minor>-<patch>`,
  merged into `develop` with a merge commit (history: `git log --first-parent develop`).
- Our history was created from a one-time import: it shares **no common ancestor** with the real upstream graph.
  That is why `custom_scripts/sync_upstream` exists (see §4).
- The upstream release tags (`v17.9.1`, ...) are available locally after `git fetch upstream --tags`, which is what
  makes every comparison below possible.

## 2. How Enterprise restrictions work (mental model)

OpenProject has no single "license check". A feature is restricted by *each* place that asks
`EnterpriseToken.allows_to?(:feature_key)` (or an equivalent). We removed every such place by hand, so
**a new upstream check = a new silent restriction**. The recurring shapes:

| # | Shape | What the user sees upstream | Typical code |
|---|-------|------------------------------|--------------|
| 1 | Banner guard in a view | A banner instead of the page | `with_enterprise_banner_guard(:feature) do ... end` |
| 2 | Banner only | Upsell box above working UI | `render EnterpriseEdition::BannerComponent.new(:feature)` |
| 3 | Controller guard | Redirect / 402 / flash | `guard_enterprise_feature(:feature)`, `before_action :require_ee`, `render_402` |
| 4 | Contract validation | "Only available in Enterprise" error on save | `RequiresEnterpriseGuard`, `errors.add ..., :enterprise_plan_required` |
| 5 | Disabled UI | Greyed inputs/buttons with crown icon | `disabled: !EnterpriseToken.allows_to?(:f)`, `op-enterprise-addons` |
| 6 | Model/helper predicate | Feature silently off | `Status.can_readonly?`, `feature_available?`, `Timestamp.allowed` |
| 7 | Settings gate | Setting not writable | `writable: -> { EnterpriseToken.allows_to?(:f) }` |
| 8 | Seat limit | "User limit reached" | `OpenProject::Enterprise.user_limit_reached?` |
| 9 | Menu/module metadata | Crown icon in menus/tabs | `enterprise_feature: "..."` on menu/project_module |
| 10 | Frontend gate | Angular banner/disabled control | `BannersService.allowsTo()`, `configuration.availableFeatures` |
| 11 | Outbound trial/billing traffic | Calls to openproject.com services | trial host, Chargebee in CSP |

The machine-readable version of this table is `restriction_patterns.tsv`; the full list of what we removed is in the
registry §1.2.

## 3. Tooling you need

| Tool | Use | Notes |
|------|-----|-------|
| Git >= 2.30 | merge, diff, range-diff, `git replace` | `git config rerere.enabled true` is recommended (remembers conflict resolutions between releases) |
| Python 3 | `custom_scripts/enterprise_audit.py` | standard library only |
| Ruby 4.0.6 (`.ruby-version`), Bundler, Node ^24.15 | boot app, rubocop, erb_lint, eslint, specs | see root `AGENTS.md` |
| PostgreSQL / Docker | run the app for a smoke test | `docker/dev/AGENTS.md`, or `bin/dev` |
| A diff/merge GUI | review conflicts and diffs | JetBrains IDE (RubyMine / IntelliJ), VS Code, Sourcetree + Apple FileMerge (`opendiff`, already configured as git `difftool.sourcetree`/`mergetool.sourcetree`), Meld, Beyond Compare, Kaleidoscope |
| GitHub compare page | read what upstream changed | `https://github.com/opf/openproject/compare/v<OLD>...v<NEW>` |
| GitLab compare page | read what we changed | `https://git.bethelservice.org/cdsupportdevelopers/general/openproject/-/compare/v<NEW>...develop` after fetching the upstream tag, or use local git |
| Upstream release notes | spot new Enterprise add-ons | `docs/release-notes/<version>/README.md` (in the tag) and openproject.org release notes |

## 4. Release workflow (step by step)

Let `P` = version we are on (`grep -E 'MAJOR|MINOR|PATCH' lib/open_project/version.rb`) and `X` = new upstream tag.

```bash
git checkout develop && git pull
git checkout -b code-maintenance/op-<ticket>-changes-from-v<X-with-dashes>
git fetch upstream --tags
git config rerere.enabled true

# 0. baseline is healthy before you start (all must be green)
python3 custom_scripts/enterprise_audit.py verify
python3 custom_scripts/enterprise_audit.py scan

# 1. what is going to hurt? (HEAD must still be P + our changes)
python3 custom_scripts/enterprise_audit.py upstream-impact vP vX | tee /tmp/impact-vX.txt
git diff --diff-filter=A --name-only vP vX -- 'modules/*/lib/*/engine.rb'   # brand-new modules

# 2. merge (left uncommitted on purpose)
custom_scripts/sync_upstream vP vX            # real 3-way merge via a temporary graft
#   or, as recent branches did:  git merge vX   (works once earlier tag merges created common ancestors;
#   if Git answers 'refusing to merge unrelated histories', use sync_upstream)
# resolve conflicts -> git add -> review -> commit -> custom_scripts/sync_upstream --cleanup
```

Notes on `custom_scripts/sync_upstream`:

- Its header comment says `script/sync_upstream` - the real path is **`custom_scripts/sync_upstream`**.
- It needs a clean working tree and the `upstream` remote. It temporarily rewrites how Git *sees* HEAD
  (`git replace --graft`), never rewrites commits, and leaves the merge uncommitted.
- After committing the merge run `custom_scripts/sync_upstream --cleanup`. Never push `refs/replace/*`.
- If the graft cannot create a common ancestor it aborts; your branch must really be `P` + customizations.

Then continue:

```bash
# 3. conflict policy
#   file listed in registry §1-§3  -> take upstream's new code, re-apply our removal/patch
#   anything else                  -> take upstream

# 4. prove nothing of ours was lost, find new restrictions
python3 custom_scripts/enterprise_audit.py verify           # must be 100%
python3 custom_scripts/enterprise_audit.py scan             # NEW / GROWN hits = work to do
python3 custom_scripts/enterprise_audit.py delta-diff vP vX # (while merge is uncommitted) our delta before vs after

# 5. fix, then quality gates
bin/dirty-rubocop --uncommitted
erb_lint $(git diff --name-only --diff-filter=AM HEAD -- '*.erb')
(cd frontend && npx eslint $(git diff --name-only --diff-filter=AM HEAD -- 'frontend/src/*.ts' | sed 's#^frontend/##'))
bundle exec rails zeitwerk:check

# 6. update the knowledge base (registry, invariants, patterns, baseline), update docker/prod/Dockerfile-slim
git commit -m "Merge tag 'vX' into code-maintenance/op-<ticket>-changes-from-v<X>"   # + fix commits, see §9
```

## 5. Per-release review checklist

Copy this list into the maintenance ticket.

**A. Before merging**
- [ ] Working tree clean, on the maintenance branch, `upstream` tags fetched.
- [ ] `verify` and `scan` are green on the *current* code (otherwise you inherit unknown debt).
- [ ] Read upstream release notes for **Enterprise add-on** labels and new modules/settings.
- [ ] `upstream-impact vP vX` saved; sections 1 and 2 read.

**B. Merge**
- [ ] `sync_upstream` (or merge) done, every conflict resolved per policy, nothing committed blindly.
- [ ] `docker/prod/Dockerfile` (upstream) vs `docker/prod/Dockerfile-slim` (ours): ported Ruby/Node/npm/Debian/
      hocuspocus bumps and any changed build steps (setup scripts under `docker/prod/setup/`).
- [ ] `.gitlab-ci.yml`, `custom_scripts/*` still compatible (see §6).

**C. Restrictions** (the core of the job)
- [ ] `enterprise_audit.py verify` = all invariants hold.
- [ ] `enterprise_audit.py scan` = no NEW/GROWN hits left (each either removed or consciously baselined).
- [ ] Manual sweep of [AGENT_PLAYBOOK §5](AGENT_PLAYBOOK.md#5-finding-restrictions-the-scanner-does-not-know-yet):
      new feature keys, `ee.upsell` locale keys, new settings with `writable:` lambdas, new modules, frontend gates.
- [ ] `git grep -n "guard_enterprise_feature"` returns nothing (otherwise Rails will not boot).
- [ ] No new `with_enterprise_banner_guard` / `EnterpriseToken.allows_to?` outside the baselined infrastructure.
- [ ] Registry §1.3 re-evaluated (did upstream change the areas of the resolved fixes? invariants cover them).

**D. Custom code**
- [ ] `enterprise_audit.py markers` - every `OP-CUSTOM` / `CUSTOM CHANGE` block survived and still makes sense
      (upstream may have fixed the issue: then remove ours).
- [ ] GitLab integration module: migrations still ordered/applied, routes/API mount points unchanged in upstream
      `engine.rb`, hardcoded status ids `483`/`488` (registry C-2) still valid in the target DB.
- [ ] `delta-diff` reviewed: no unexpected **DROPPED**; every **CHANGED/NEW** file explained.

**E. Runtime smoke test** (admin user, **no** token, banners hidden) - see §7 for the list.

**F. Wrap-up**
- [ ] Registry updated (new removals, version stamp), `invariants.tsv`/`restriction_patterns.tsv`/`known_residuals.tsv` updated.
- [ ] Commits follow `AGENTS.md` (first line < 72 chars, reference the work package).
- [ ] CI pipeline builds `openproject-slim`; deploy to dev first, then prod.

## 6. Custom scripts (`custom_scripts/`)

| Script | What it does | Runs where | What to re-check on a new OpenProject version |
|--------|--------------|-----------|----------------------------------------------|
| `sync_upstream` | Bash. Merges an upstream tag into our unrelated history using a temporary `git replace --graft`, merge left uncommitted. `--cleanup` removes the graft. | developer machine | Nothing version specific. Needs remote `upstream`, clean tree. |
| `enterprise_audit.py` | Python 3 helper of this kit: `scan`, `verify`, `upstream-impact`, `delta-diff`, `markers`. | developer machine / agent / optionally CI | Update data files in `custom_maintenance/`, not the code, when patterns change. |
| `get_version.py` | CI job `extract_version`. Reads `MAJOR/MINOR/PATCH` from `lib/open_project/version.rb`, counts existing tags `X.Y.Z-N`, creates `X.Y.Z-(N+1)` (git tag + GitLab API tag on `$CI_COMMIT_REF_NAME`), writes `version.env` (`APP_VERSION`) for the build. Needs `GITLAB_API_TOKEN`, `CI_COMMIT_REF_NAME`, `python-gitlab`. | GitLab CI on `develop` | After a version bump the counter restarts at `-1` automatically. Make sure `version.rb` was merged, otherwise the old version number is re-tagged. |
| `ldap_sync.py` | Scheduled pipeline job (`schedule:ldap_sync`). For every OpenProject group (API v3) with the same name in Active Directory (`ldap://bethel.jw.org`), reads LDAP members and PATCHes the OpenProject group membership. Env: `LDAP_PASSWORD` (base64), `ADMIN_OP_TOKEN`. TLS verification disabled (`verify=False`), user matching by full name. | GitLab schedule | Depends on API v3 `/groups` and `/users` filters (`name`). Re-test only if release notes mention API v3 group/user changes. Known weak points: name-based user matching, `verify=False`. |
| `migrate_gitlab_to_openproject.py` | One-shot/resumable migration of GitLab issues (+ comments, images, attachments, milestones -> versions) to OpenProject work packages. Configuration is edited at the top of the file (tokens are blank in git - **never commit tokens**). Resumes through `migration_progress.json`. Contains hardcoded project/type/category/custom field ids (e.g. custom field `193`, project `95`). | operator laptop | Rarely affected; re-check only API v3 work package/attachment/version endpoints if used again. |

The pipeline itself (`.gitlab-ci.yml`) builds `docker/prod/Dockerfile-slim` (target `slim`) on `develop` and runs
LDAP sync on schedules. `get_version.py` assumes `lib/open_project/version.rb` keeps the `MAJOR =`/`MINOR =`/`PATCH =` form.

## 7. Runtime smoke test (no token installed)

Log in as admin, with `Administration` visible, and check **no crown icons, upsell banners, disabled controls, 402/403/redirects**:

1. Admin -> Custom fields: create hierarchy, weighted item list; (projects) calculated value.
2. Admin -> Work packages -> Types -> Form configuration: add/rename/delete groups; Defaults tab: automatic subjects; Statuses: "read-only".
3. Admin -> Workflows / custom actions (create one) / Design (custom style, upload logo, favicon) / Attachments -> virus scanning tab.
4. Admin -> Authentication: SAML, OpenID Connect (add provider), SCIM clients, LDAP groups & departments sync; Settings -> external links capture.
5. Admin -> AI / MCP configuration; Time & costs -> time restrictions; File storages: Nextcloud SSO, OneDrive/SharePoint; Wikis (XWiki).
6. Projects: portfolios and programs (create, list, menu); project life cycle definitions; project creation wizard.
7. Work packages: share dialog (work package sharing), "shared with me" lists, baseline comparison (any date), PDF Gantt export, internal comments, read-only status.
8. Modules: team planner, resource management, meeting templates, backlogs (sprint sharing, multiple active sprints), boards, GitLab tab (create MR/issue).
9. Users: invite placeholder users; members page seat counter; user count header has no limit text.
10. Browser console/network: no calls to `*.openproject.com` trial/Chargebee endpoints.

## 8. Comparing changes: how to review what an agent (or a person) did

There are always **three patches** in play. Name them once and compare the right pair:

| Lens | Meaning | Command |
|------|---------|---------|
| **U** upstream change | what OpenProject changed between releases | `git diff vP vX` |
| **C** our customization | what we differ from an upstream tag | `git diff vX` (working tree vs tag) or `git diff vX HEAD` (committed) |
| **D** delta of C | how our customization changed during the merge | `enterprise_audit.py delta-diff vP vX` |

### 8.1 Git (works everywhere)

```bash
# our whole customization against the new upstream, limited to a feature area
git diff vX -- app/components modules/storages
git diff --stat vX | tail -1                       # size of customization; should barely grow
git diff -w --color-moved=dimmed-zebra vX -- app/views/admin   # ignore re-indentation, see moved blocks

# only what is NEW compared with what we had before the merge (merge still uncommitted)
git diff --cached HEAD --stat                      # full merge result, staged
git diff HEAD -- <file>                            # merge result vs previous develop

# why is this line like this? who removed the guard?
git log -S'user_limit_not_exceeded' --oneline -- app/contracts/users
git log -p --follow -- app/models/status.rb
git blame -w -C -C vX..HEAD -- app/models/status.rb

# compare two maintenance rounds of the same customization (patch vs patch)
git range-diff <old-merge-base>..<old-tip> <new-base>..<new-tip>

# restore a file to upstream or to our previous version
git checkout vX -- <file>              # pure upstream (loses our removal!)
git checkout HEAD -- <file>            # previous develop version
git merge-file -p ours.rb base.rb theirs.rb   # manual 3-way
```

During a conflicted merge, `git checkout --conflict=diff3 <file>` shows base/ours/theirs markers; `git show :1:<file>`
(base), `:2:` (ours = our develop), `:3:` (theirs = upstream) give the three versions for any external tool.

### 8.2 JetBrains IDEs (RubyMine / IntelliJ - `.idea` is already present locally)

- *Git -> Compare with Branch/Tag...* -> choose `vX`; the tool window lists **exactly our customization**
  (changed files only), double-click for the side-by-side diff. This is the quickest "what do we differ in" view.
- Right-click a file/folder -> *Git -> Compare with...* for a revision; *Show History* + *Compare with Local*.
- Conflicts: *Git -> Resolve Conflicts*. Use the three-pane merge dialog: left = ours (develop), right = upstream,
  centre = result. Use *Apply non-conflicting changes* then handle the rest by hand; the "magic wand" is safe only
  for hunks that do not touch our removals.
- *Local History* rescues an accidental revert; *Annotate with Git Blame* with "ignore whitespace" for re-indented blocks.
- Turn on *Settings -> Version Control -> Git -> "Ignore whitespace" in diffs* when reviewing banner-guard removals,
  because unwrapping a block re-indents dozens of lines.

### 8.3 VS Code

- GitLens: *Compare References...* (tag `vX` vs `HEAD`), or Git Graph for visual history. Built-in 3-way *Merge Editor*
  for conflicts. Setting `diffEditor.ignoreTrimWhitespace: true` for reindent noise.

### 8.4 Sourcetree / FileMerge / Meld / Beyond Compare / Kaleidoscope

- This machine's `.git/config` already maps `difftool.sourcetree` and `mergetool.sourcetree` to Apple `opendiff`.
  `git difftool -d vX` opens a **directory diff** of our tree vs the tag (all customizations at once);
  `git mergetool` opens FileMerge with `-ancestor $BASE` for 3-way merges.
- Meld/Beyond Compare: `git config diff.tool meld && git difftool -d --no-symlinks vX` (directory mode).

### 8.5 Recommended review recipe for an agent-produced merge

1. Let the agent work on the maintenance branch, uncommitted or in separate commits (one for the merge, one per
   restriction removal, one for knowledge-base updates).
2. `python3 custom_scripts/enterprise_audit.py delta-diff vP vX` - review **DROPPED** first (lost customization), then
   **CHANGED**, then **NEW**. For each file: `git diff vX -- <file>` (our delta now) next to `git diff vP HEAD -- <file>` (our delta before).
3. `git diff -w --color-moved vX -- <new files>` for the NEW category: confirm each is a restriction removal of the
   documented shape (registry §1.2) and not collateral edits.
4. `python3 custom_scripts/enterprise_audit.py verify` and `scan` yourself (do not trust the report).
5. Spot check 3-5 removals in the app UI as admin (§7).
6. Skim `git diff --stat vX` size: it should grow only by the new removals.
7. Read the knowledge-base diff (`custom_maintenance/`); reject commits that baseline NEW hits without explanation.

### 8.6 Checking that an invariant really detects the restriction

```bash
git worktree add ../op-upstream-vX vX        # pristine upstream checkout (read-only reference)
cp -r custom_maintenance ../op-upstream-vX/ && mkdir -p ../op-upstream-vX/custom_scripts \
  && cp custom_scripts/enterprise_audit.py ../op-upstream-vX/custom_scripts/
(cd ../op-upstream-vX && python3 custom_scripts/enterprise_audit.py verify)   # expect violations
git worktree remove --force ../op-upstream-vX
```

## 9. Commit and review conventions

- Branch `code-maintenance/op-<ticket>-changes-from-v17-10-0`; merge to `develop` with a merge commit.
- Commit subjects < 72 chars; reference the work package; suggested split:
  `Merge tag 'vX' ...` (merge) / `Remove new enterprise restrictions from vX` / `Update maintenance docs for vX`.
- Mark any new non-EE patch with `# OP-CUSTOM:` and register it (registry §2).

## 10. Hardening ideas (not applied; decide as a team)

These would reduce recurring effort but widen the delta from upstream, so they are **proposals only**:

1. Make `with_enterprise_banner_guard` always `yield` (and render no banner) - removes the most dangerous silent-hide
   pattern for future views with a 1-line change in `app/helpers/enterprise_helper.rb`.
2. Restore a tiny `guard_enterprise_feature` no-op macro in `Accounts::EnterpriseGuard` so new upstream calls do not
   break boot (today a boot failure is the signal; a no-op would hide it - the scanner would still list it).
3. Making `EnterpriseToken.allows_to?` return `true` would unlock nearly everything with one edit and make new
   upstream checks harmless, but it departs from the current per-call-site approach (less selective, and the
   token model/gem stay untouched today by design). A team decision, not an agent decision.
