# Agent Playbook - keeping the "all features unlocked" OpenProject fork current

Audience: an AI coding agent (Claude Code or similar) starting from zero context.
Read this file completely, then [CUSTOMIZATIONS_REGISTRY.md](CUSTOMIZATIONS_REGISTRY.md). Humans: see [HUMAN_GUIDE.md](HUMAN_GUIDE.md).

## 1. Mission and ground rules

Never modify, add or restore `spec/**` files (specs are not run here and EE assertions in them are ignored).

This repository is an internal fork of upstream OpenProject (`github.com/opf/openproject`, remote `upstream`).
Goal: **every Community and Enterprise feature works with no Enterprise token installed**. After each upstream
release you (a) integrate the release, (b) find any *new* Enterprise restriction, (c) remove it surgically,
(d) prove nothing of ours was lost, (e) record what you learned.

Rules:

1. **Surgical**: change the minimum lines that lift the restriction. No refactors, no reformatting, no "cleanup"
   of unrelated code, no renaming. Keep the diff against upstream as small as the existing removals.
2. **Do not fake a token** and do not touch `EnterpriseToken`, `OpenProject::Token` or the token gem. The fork's
   approach is to delete/neutralise each guard at its call site.
3. **Remove the dead code you orphan** (unused banner render, unused parameter, unused private method, now-unused
   `include`). Leave the shared EE infrastructure listed in the registry §0 alone.
4. **Never revert a customization while resolving a merge conflict.** `custom_scripts/enterprise_audit.py verify`
   must pass before you finish.
5. **Mark non-EE customizations** (bug fixes, behaviour changes) in code with `# OP-CUSTOM: <reason>` or the
   `CUSTOM CHANGE (BEGIN)/(END)` block style already used, so humans and `enterprise_audit.py markers` find them.
   Do not add markers to plain EE guard removals (hundreds of lines; the registry and `git diff` document them).
6. Follow the repo rules in `AGENTS.md` (few comments, commit message format, copyright headers, rubocop/erb_lint).
7. Do **not** commit, push, merge to `develop` or create tags unless the user asks. Prepare a branch/working tree.
8. Outward-facing or irreversible actions (push, force operations, `git replace` grafts left behind, deleting
   branches) need explicit user confirmation.

## 2. Toolbox (all paths relative to repo root)

| Tool | Purpose |
|------|---------|
| `python3 custom_scripts/enterprise_audit.py scan` | finds every hit of every known restriction pattern; compares with `custom_maintenance/known_residuals.tsv` |
| `python3 custom_scripts/enterprise_audit.py verify` | checks `custom_maintenance/invariants.tsv` (our customizations still present) |
| `python3 custom_scripts/enterprise_audit.py upstream-impact <old> <new>` | BEFORE merging: files upstream touched that we customized + restriction hits upstream ADDED |
| `python3 custom_scripts/enterprise_audit.py markers` | lists `OP-CUSTOM` / `CUSTOM CHANGE` markers |
| `custom_scripts/sync_upstream <from_tag> <to_tag>` | grafts HEAD onto `from_tag` and runs a real 3-way `git merge --no-commit` (see HUMAN_GUIDE §4) |
| `custom_maintenance/restriction_patterns.tsv` | the pattern catalog (id, regex, description, recipe) |
| `custom_maintenance/invariants.tsv` | present/absent assertions per file |
| `custom_maintenance/known_residuals.tsv` | triaged baseline of residual hits (`file  pattern_id  count`) |

## 3. Procedure for a new upstream release `X` (previous release `P`)

State your plan to the user first when the merge itself is requested; the steps below assume permission to modify
the working tree on a maintenance branch.

1. **Orient.** `git status` must be clean. `git describe`/`grep -E 'MAJOR|MINOR|PATCH' lib/open_project/version.rb`
   tells the current base (`P`). Branch convention: `code-maintenance/op-<ticket>-changes-from-v<X-with-dashes>`.
   `git fetch upstream --tags`. If `<X>` is unknown to the user, read `docs/release-notes/<X>/` upstream.
2. **Pre-merge analysis** (HEAD = P + customizations):
   `python3 custom_scripts/enterprise_audit.py upstream-impact vP vX` and keep the output. Section 1 = conflict-prone
   files; section 2 = new restriction hits to remove. Also read upstream release notes for features labelled
   *Enterprise add-on*.
3. **Merge** with `custom_scripts/sync_upstream vP vX` (preferred; real 3-way merge, left uncommitted) or
   `git merge vX` as past maintenance branches did. Resolve conflicts with this priority:
   - file in registry §1-§3 -> take upstream's new code, then **re-apply our removal/patch** (do not keep the old
     side wholesale; upstream may have refactored the surrounding code);
   - everything else -> take upstream.
   Use `git diff vX -- <file>` (our remaining delta vs the new upstream) to confirm the delta is only ours.
4. **Verify customizations survive:** `python3 custom_scripts/enterprise_audit.py verify`. Fix every VIOLATED row by
   re-applying the change (the `why` column says what it protects).
5. **Hunt new restrictions:** `python3 custom_scripts/enterprise_audit.py scan`. For each NEW/GROWN hit open the
   file, understand the gate, remove it with the matching recipe (§4), and re-run until clean. For hits that are
   unused EE infrastructure, add them to the baseline (§7) instead of editing.
6. **Manual sweep for patterns the scanner cannot know yet** (§5). New release notes, new `modules/*`, new
   admin settings, new API errors, and `git diff vP vX --stat -- modules/` for brand-new modules.
7. **Re-apply non-EE customizations** (registry §2, §3): check `markers`, GitLab module, Dockerfile-slim vs upstream
   `docker/prod/Dockerfile` (port version bumps), `.gitlab-ci.yml`.
8. **Quality gates** (run what the environment allows; report what you could not run):
   `bin/dirty-rubocop --uncommitted`, `erb_lint <changed .erb>`, `cd frontend && npx eslint <changed files>`,
   `bundle exec rails zeitwerk:check`, and targeted specs for files you touched
   (`bundle exec rspec <path>`). Note: upstream specs that assert EE behaviour are known to be stale (registry F-8).
   A Rails boot that fails with `undefined method 'guard_enterprise_feature'` means a new upstream controller guard
   (recipe R1) - that is a *good* early signal.
9. **Update the knowledge base** (§7): registry, invariants, patterns, baseline.
10. **Report** to the user: new restrictions found/removed (file + feature), conflicts resolved, customizations
    re-applied, anything unverified, and the open findings (registry §1.3). Never claim a runtime check you did
    not perform.

## 4. Recipes: how each restriction pattern is removed

Pattern ids refer to `restriction_patterns.tsv`. After any recipe, grep for the symbol you orphaned.

**R1 - Controller guard / hard failure** (`GUARD_MACRO`, `HTTP_402`, `UPSELL_ROUTE`)
- Delete `guard_enterprise_feature(:x ...) { ... }`, `before_action :require_ee / check_ee / require_enterprise_token / ...`
  and the private method it called.
- Delete the matching `upsell` / `share_upsell` action, its view, its route and its entry in
  `config/initializers/permissions.rb` / the module `engine.rb` permission list (otherwise routes point to nothing).
- Remove `render_402` / `MissingEnterpriseToken` branches; keep the surrounding behaviour of the allowed path.

**R2 - Predicate/model/helper gate** (`ET_CHECK`, `ET_REF`, `CAN_FLAGS`, `TOKEN_PLAN`, `SSO_FILTER`)
- `A && EnterpriseToken.allows_to?(:f)` -> `A`; `EnterpriseToken.allows_to?(:f) ? a : b` -> `a`;
  `return unless EnterpriseToken.allows_to?(:f)` -> delete the line; `... || EnterpriseToken...` -> the other side.
- A method whose body becomes constant: keep the method with the permissive constant (`true`) when it has many
  callers (precedent: `allowed_to_customize_life_cycle?`, `feature_available?`), delete it when the callers are few
  and you remove them in the same change.
- API representers: remove `show_if:` / `if:` lambdas that only test the token.
- Do not edit the token model or the gem.

**R3 - Banner guard in a view** (`BANNER_GUARD`, `BANNER_COMP`)
- `with_enterprise_banner_guard(:f, ...) do ... end` -> keep only the block body and **re-indent it** (this is the
  most common and the most dangerous pattern: unmodified, it hides the whole feature content because the block
  only yields when the token allows it).
- `render EnterpriseEdition::BannerComponent.new(:f, ...)` / `EnterpriseEdition::TrialTeaserComponent` -> delete
  the render (and a now-empty wrapper row).
- Watch for `inactive_guard:` / `else` branches rendering a read-only variant: keep the "allowed" branch only.
- Keep the wrapper-free diff small: if re-indentation makes a huge hunk, that is accepted precedent
  (e.g. `_sso.html.erb`, `projects/new.html.erb`).

**R4 - Contract validation** (`CONTRACT_GUARD`, `CONTRACT_PLAN`)
- `include RequiresEnterpriseGuard` + `self.enterprise_action/condition` -> delete the include and assignments
  (the module is a no-op, so this is optional hygiene; do it when you touch the file anyway).
- Delete custom `validate :...enterprise...` and its method; delete `errors.add ..., :enterprise_plan_required`.
- UI forms that mirror the contract (`disabled: readonly? || !enterprise?`) lose the enterprise term.

**R5 - User/seat limits** (`USER_LIMIT`)
- `OpenProject::Enterprise.user_limit` is patched to `999999`, so `user_limit_reached?` is false and most code is
  inert. Still remove limit-triggered branches in controllers/contracts/API/jobs when they would show warnings,
  stop synchronisation, or redirect. Seat counters in markup use the literal `999999`
  (`members/_member_form.html.erb`).

**R6 - Menu/tab/format metadata and icons** (`FEATURE_META`, `UPSELL_ICON`)
- `enterprise_feature:` keys on `menu.push`, `project_module`, tabs, `CustomFieldFormat.register` are ignored by the
  current consumers (they were removed) - removal is optional hygiene. If a **new** consumer appears in upstream
  (for example a new `if feature && !EnterpriseToken...` render), remove that consumer instead.
- Delete trailing crown icons (`with_trailing_visual_icon(icon: :"op-enterprise-addons" ...)`,
  `class: "upsell-colored"`).

**R7 - Disabled inputs / read-only settings** (`SETTING_GATE`)
- Remove `disabled: !EnterpriseToken...` from inputs and `writable: -> { EnterpriseToken... }` from
  `config/constants/settings/definition.rb` (`writable: true`).

**R8 - Frontend** (`FRONTEND_BANNERS`)
- Prefer **no edit** when the code goes through `BannersService` (already permissive, registry A-C6).
- Direct readers of `configuration.availableFeatures` / `triallingFeatures` must be fixed locally (precedent: onboarding tour, F-1).
- Remove imports/registrations of `OpenprojectEnterpriseModule` only when the module's last consumer is removed
  (precedent: boards, user-preferences, work-packages, grids modules).
- Angular templates using `<op-enterprise-banner-frame>` need no change (never visible).

**R9 - Outbound upsell/trial/billing traffic and links** (`TRIAL_SERVICES`, `STATIC_UPSELL_LINKS`)
- Empty the trial host/chargebee/plan settings (done), drop domains from the CSP (done) and delete upsell links
  from `config/static_links.yml` only when their last consumer was removed (an unknown link key raises at render).

## 5. Finding restrictions the scanner does not know yet

Scanner coverage is a floor, not a ceiling. After the scan, always sweep manually:

1. **New feature keys.** In the new tag run `git grep -ohE "allows_to\?\(:[a-z_]+\)|guard_enterprise_feature\(:[a-z_]+|BannerComponent\.new\(:[a-z_]+|with_enterprise_banner_guard\(\s*:[a-z_]+" vX -- app lib modules`
   and compare the key list with registry §1.2. Any key not in the registry is new.
2. **Release notes / docs.** `docs/release-notes/<X>/README.md` and `docs/system-admin-guide` pages labelled
   "Enterprise add-on" or `enterprise-add-on` anchors; `config/static_links.yml` `enterprise_features:` keys.
3. **Locale hints.** New keys under `ee.upsell.*` / `*.upsell.*` / `enterprise_plan_required` in `config/locales/en.yml`
   and `modules/*/config/locales/en.yml` reveal new gated features (each upsell string belongs to a banner).
4. **Behavioural gates that do not mention the token**: `Setting.*` defined with `writable: -> {` lambdas,
   plan-based `OpenProject::Token.lowest_plan_for`, `disabled:` expressions on new form inputs, new API schema
   `show_if` lambdas, `User.current.admin? && ...ee...`, license-dependent limits (counts, sizes, seats).
5. **New modules.** `git diff --stat vP vX -- modules/` (added directories). Check their `engine.rb`
   (`project_module ... enterprise_feature:`, `menu ... enterprise_feature:`), controllers and views.
6. **Frontend.** `git grep -nE "availableFeatures|trialling|BannersService|enterprise" vX -- frontend/src/app modules/*/frontend`.
7. **Runtime proof when possible.** `bin/dev` (or Docker, see `docker/dev/AGENTS.md`) as admin with *no token*: open
   Administration -> every EE page listed in registry §1.2 and check there is no banner, crown icon, disabled button
   or redirect; create one object of each gated type.

## 6. Anatomy of a typical new restriction (worked example)

Upstream adds, in a view:

```erb
<%= with_enterprise_banner_guard(:shiny_feature, variant: :large, image: "enterprise/shiny.png") do %>
  <%= render ShinyComponent.new %>
<% end %>
```

and in the controller `guard_enterprise_feature(:shiny_feature, only: %i[create])`, in a contract
`include RequiresEnterpriseGuard; self.enterprise_action = :shiny_feature`.

Fix: view -> `<%= render ShinyComponent.new %>`; controller -> delete the macro line (otherwise boot error);
contract -> delete include and assignment (hygiene). Then `scan` shows the key under no pattern anymore; add
nothing to the baseline; add a row to registry §1.2 and, if a file-level invariant is cheap
(`controller` `absent` `guard_enterprise_feature`), a row to `invariants.tsv`.

## 7. Recording new knowledge

The kit only works if it is updated in the same change set that introduces the knowledge.

**a) New restriction implemented in a way no pattern matches** (a new idiom, e.g. a new helper like
`require_feature!(:x)` or a new settings flag):
1. Append a row to `restriction_patterns.tsv`: `ID<TAB>regex<TAB>description<TAB>recipe` (Python regex, one line,
   TABs between columns). Use an ID in UPPER_SNAKE_CASE. Add a new recipe section (R10, R11...) in §4 if none fits.
2. Run `python3 custom_scripts/enterprise_audit.py scan`; it will list every site of the idiom as NEW.
3. Remove the restrictions (recipes). Residual hits that are unused infrastructure -> baseline.
4. Add the idiom to §5 if it needs manual discovery hints.

**b) New customization (anything that differs from upstream on purpose)**
1. Registry: add a row in §1.2 (EE feature) or §2/§3 (other), with file paths and rationale.
2. `invariants.tsv`: add a `present`/`absent` assertion that fails on pristine upstream and passes on our tree
   (prove it: it must be violated by the upstream file - e.g. `git show vX:<file> | python3 -c ...` or the worktree
   trick in HUMAN_GUIDE §8). Keep regexes single-purpose and robust to re-indentation (`\s+`).
3. Non-EE behaviour changes get an `OP-CUSTOM` marker in code.

**c) Baseline (`known_residuals.tsv`)** only after triage: `python3 custom_scripts/enterprise_audit.py scan --update-baseline`
rewrites it from the current tree. Never refresh it to silence an unreviewed NEW hit.

**d) A customization that upstream made obsolete** (they implemented the same thing): delete our version, delete
its invariant and registry row, mention it in the report.

**e) Version stamp**: update the "Baseline of this document" line at the top of the registry
(`fork at vX.Y.Z`, date, develop commit) when a release is integrated.

## 8. Things that look like restrictions but are not (do not "fix")

- Permission checks (`User.current.allowed_in_project?`, `allowed_globally?`, `authorize`) - normal RBAC.
- `Setting.*_writable?` returning false because the value comes from an ENV var - deployment configuration.
- `ee_hide_banners`, `OpenProject::Enterprise.user_limit = 999999`, the no-op `RequiresEnterpriseGuard` - our own neutralisations (registry §1.1).
- Feature flags (`OpenProject::FeatureDecisions`) - upstream rollout switches, unrelated to licensing; enable only
  if the user asks.
- `spec/**` references to `EnterpriseToken` (test support).

## 9. Output contract for the final report

```
Release: P -> X  (branch ...)
Conflicts: <files> -> how resolved
New EE restrictions removed: <feature key | file:line | recipe>
Customizations re-applied: <registry ids>
Verify: <N/M invariants>  Scan: <new hits 0 | list>
Checks run: rubocop/erb_lint/eslint/specs (what passed, what could not run)
Open findings: <registry F-ids and new ones>
Knowledge base updated: <files>
```
