# Customizations Registry

> Source of truth for **every deliberate difference** between this fork and upstream OpenProject.
> Baseline of this document: fork at **v17.9.1** (develop @ `393c1c22bff`, 2026-10-02), compared with the
> upstream tag `v17.9.1` (`git diff v17.9.1 HEAD`: 310 files, 70 added / 240 modified).
>
> Keep it current: every time a customization is added, moved or dropped, update this file **and**
> `invariants.tsv` (see [AGENT_PLAYBOOK.md §7](AGENT_PLAYBOOK.md#7-recording-new-knowledge)).

Quick reproduction of the numbers above:

```bash
git diff --stat v17.9.1 HEAD -- . ':!custom_scripts' ':!custom_maintenance' ':!modules/gitlab_integration'   # EE removals + small fixes
git diff --name-status v17.9.1 HEAD | grep '^A'                                                              # files that do not exist upstream
```

## 0. Philosophy of the fork

1. **Enterprise token model is untouched** (`app/models/enterprise_token.rb`, `OpenProject::Token`): with no
   token installed, `EnterpriseToken.allows_to?(anything)` is `false`. The fork does **not** fake a token.
2. Instead, **every place that consults the token was edited locally** ("surgical removal"): the guard is deleted
   or replaced with the permissive branch, and the now-dead code (banner, icon, parameter, helper) is removed.
3. Consequence: **any new upstream code that checks the token silently re-introduces a restriction** (a hidden
   button, a disabled input, a missing feature) - there is no central switch. Finding those new checks after each
   release is the main job (see [HUMAN_GUIDE.md](HUMAN_GUIDE.md)).
4. A few restrictions were neutralised **centrally** (cheap safety nets, listed in §1.1).

Residual EE infrastructure that is deliberately left in place (unused or inert): the `EnterpriseToken` model and
controller, `EnterpriseEdition::*` / `EnterpriseTrials::*` components, `EnterpriseHelper`, `Accounts::EnterpriseGuard`
(no longer included anywhere), `RequiresEnterpriseGuard` (now a no-op module), the `/enterprise_tokens` admin page
(menu entry removed, URL still routable), `config/initializers/ee_token.rb`. They are baselined in
`known_residuals.tsv`. Do **not** delete them (large upstream conflict surface, no benefit).

---

## 1. Category A - Enterprise restriction removals

### 1.1 Central switches (single point, wide effect)

| ID | File | Change | Effect |
|----|------|--------|--------|
| A-C1 | `config/constants/settings/definition.rb` | `ee_hide_banners` default `false` -> `true` | `EnterpriseToken.hide_banners?` is true, so `EnterpriseEdition::BannerComponent#render?` is false (unless `show_always:`) |
| A-C2 | `app/helpers/application_helper.rb` | `css << "ee-banners-hidden"` unconditional | CSS also hides banners |
| A-C3 | `lib/open_project/enterprise.rb` | `user_limit` -> `999999` (was `delegate :user_limit, to: EnterpriseToken`) | `user_limit_reached?` never true; seat counters never block |
| A-C4 | `app/contracts/concerns/requires_enterprise_guard.rb` | `validate :has_enterprise` + method removed | any contract including `RequiresEnterpriseGuard` is a no-op |
| A-C5 | `app/controllers/application_controller.rb` | `include Accounts::EnterpriseGuard` removed | `guard_enterprise_feature` no longer exists -> a new upstream call raises `NoMethodError` at class load (loud, easy to spot) |
| A-C6 | `frontend/src/app/core/enterprise/banners.service.ts` | `allowsTo()` -> `true`, `showBannerFor()` / `trialling()` -> `false`, `onFeatureCheck` always calls `featureAvailable` | every Angular gate that goes through `BannersService` is open |
| A-C7 | `app/models/sharing_strategies/base_strategy.rb` | `feature_available?` -> `return true` | sharing strategies always available |
| A-C8 | `lib/open_project/custom_field_format.rb` | `enterprise_feature` option removed; `available?` = `enabled?` | no custom field format is gated |
| A-C9 | `config/initializers/custom_field_format.rb` | `enterprise_feature:` removed from hierarchy / weighted_item_list / calculated_value | formats creatable |
| A-C10 | `app/models/timestamp.rb` | `allowed()` returns all timestamps | baseline comparison for any date |
| A-C11 | `lib_static/open_project/configuration/helpers.rb`, `config/constants/settings/definition.rb`, `config/initializers/content_security_policy.rb` | trial host / chargebee site / plan -> `""`; chargebee + trial host removed from CSP; `appsignal-endpoint.net` removed from `connect_src` | no outbound calls to the EE trial/billing services |
| A-C12 | `lib/open_project/menu.rb`, `app/menus/submenu.rb`, `lib/redmine/menu_manager/menu_item.rb` | `show_enterprise_icon` / `enterprise_feature` / `enterprise_feature_missing?` removed | menus never show the crown icon (the `enterprise_feature:` keyword left in `menus.rb` and module engines is ignored) |

### 1.2 Feature-by-feature map

`Feature key` = what upstream passes to `EnterpriseToken.allows_to?` / banners. "Removed at" lists the sites where a guard was removed (paths relative to repo root).

| Feature key | Upstream restriction | Removed at |
|-------------|----------------------|------------|
| `virus_scanning` | admin tab icon, controller `require_ee`, disabled inputs, banner, `Setting::VirusScanning.enabled?` | `app/components/admin/attachments_settings_header_component.rb`, `app/controllers/admin/settings/virus_scanning_settings_controller.rb`, `app/views/admin/settings/virus_scanning_settings/show.html.erb`, `app/models/setting/virus_scanning.rb` |
| `calculated_values` | form guard + banner, description hidden, contract validation, row icon | `app/components/custom_fields/details_component.{rb,html.erb}`, `app/components/settings/project_custom_field*/*`, `app/contracts/custom_fields/{create,update}_contract.rb`, `config/initializers/custom_field_format.rb` |
| `custom_field_hierarchies` / `weighted_item_lists` | banner, `validate_enterprise_token` (403), format gating | `app/controllers/custom_fields_controller.rb`, `app/components/custom_fields/details_component.*`, `lib/open_project/custom_field_format{,_dependent}.rb`, `app/workers/import/jira_create_project_job/jira_import_custom_field_builder.rb` (Jira cascading select -> `hierarchy`) |
| `portfolio_management` | banners, contract validation, menu gating, filter availability | `app/contracts/projects/create_contract.rb`, `app/views/portfolios/index.html.erb`, `app/views/projects/new.html.erb`, `app/helpers/projects_helper.rb` (`portfolio_management_feature_missing?` returns `false`), `app/components/projects/index_sub_header_component.*`, `config/initializers/menus.rb`, `app/models/queries/projects/filters/ancestor_workspace_type_filter.rb` |
| `customize_life_cycle` | controller `require_enterprise_token` (402), banner | `app/controllers/concerns/projects/phase_definition_helper.rb` (returns `true`), `app/controllers/admin/settings/project_phase_definitions_controller.rb`, `app/components/settings/project_phase_definitions/index_component.html.erb` |
| `internal_comments` | contract error, journal visibility, UI banners/icons, settings page | `app/contracts/work_packages/create_note_contract.rb`, `app/models/work_package/journalized.rb`, `app/components/work_packages/activities_tab/journals/new_component.*`, `app/components/settings/project_work_packages/header_component.rb`, `app/views/projects/settings/work_packages/internal_comments/show.html.erb`, `app/forms/projects/settings/work_packages/activities/form.rb` |
| `edit_attribute_groups` | form configuration read-only, banner, contract | `app/components/work_package_types/form_configuration*` (`ee_available` parameter removed everywhere), `app/controllers/concerns/work_package_types/form_configuration_component_streams.rb`, `app/contracts/work_package_types/update_form_configuration_contract.rb` |
| `work_package_subject_generation` | disabled radio/pattern input, banner, contract | `app/forms/work_package_types/defaults_form.rb`, `app/contracts/work_package_types/update_defaults_contract.rb`, `app/forms/work_package_types/artefact_export_form.rb` (readonly removed) |
| `custom_actions` | controller guard, banner, disabled button, Angular flag | `app/controllers/custom_actions_controller.rb`, `app/views/custom_actions/index.html.erb`, `frontend/.../wp-custom-actions.component.ts` (`available = true`) |
| `define_custom_style` | controller guard, banner, `apply_custom_styles?` check, `upsell` action | `app/controllers/custom_styles_controller.rb`, `app/views/custom_styles/show.html.erb`, `app/helpers/custom_styles_helper.rb` (`skip_ee_check` parameter removed) |
| `capture_external_links` | settings `writable:` lambda, filter, controller | `config/constants/settings/definition.rb`, `lib/open_project/text_formatting/filters/external_link_capture_filter.rb`, `app/controllers/external_link_warning_controller.rb`, `app/views/admin/settings/external_links_settings/show.html.erb` |
| `project_creation_wizard` | controller `check_enterprise_plan`, banner | `app/controllers/projects/settings/creation_wizard_controller.rb`, `app/views/projects/settings/creation_wizard/show.html.erb` |
| `work_package_sharing` / `project_list_sharing` | sharing strategy, banners, menu "shared" entries, upsell pages, workflow role, warning bar | `app/models/sharing_strategies/*`, `app/components/shares/manage_shares_component.html.erb`, `app/menus/{notifications,work_packages}/menu.rb`, `app/services/work_packages/default_query_generator_service.rb`, `app/models/workflow.rb`, `app/helpers/warning_bar_helper.rb`, `app/controllers/work_packages_controller.rb` (`share_upsell` action), `config/initializers/permissions.rb`, `frontend/.../wp-share-button.html` |
| `readonly_work_packages` | `Status.can_readonly?`, disabled checkbox, banner, API schema | `app/models/status.rb`, `app/forms/statuses/form.rb`, `lib/api/v3/work_packages/{schema/work_package_schema_representer,work_package_representer}.rb` |
| `placeholder_users` | contract, invitation form, banner, index guard | `app/contracts/placeholder_users/create_contract.rb`, `app/forms/users/invitation/project_step/form.rb`, `app/models/users/Invitation/form_model.rb`, `app/views/placeholder_users/index.html.erb` |
| `gantt_pdf_export` | disabled option, 403 in helper, API representation | `app/components/work_packages/exports/pdf/export_settings_component.rb`, `app/helpers/work_packages_controller_helper.rb`, `lib/api/v3/work_packages/work_package_collection_representer.rb` |
| `baseline_comparison` | `Timestamp.allowed` (+ Angular `BannersService`) | `app/models/timestamp.rb`, A-C6 |
| `mcp_server` | banner guard, API 404, menu | `app/views/admin/mcp_configurations/index.html.erb`, `lib/api/mcp.rb`, `config/initializers/menus.rb` |
| `scim_api` | banner, button, authenticator 403, menu | `app/views/admin/scim_clients/index.html.erb`, `config/initializers/scimitar.rb`, `config/initializers/menus.rb` |
| `sso_auth_providers` | banner, disabled buttons, `check_ee`, strategy filter | `app/views/admin/settings/authentication_settings/_sso.html.erb`, `modules/auth_plugins/.../auth_plugin.rb` (`filtered_strategy?` now ends with `name = provider[:name]&.to_s`, i.e. returns the truthy name -> every strategy with a name passes; `warn_unavailable` removed), `modules/openid_connect/{controllers/providers_controller,views/providers/index,lib/.../engine}`, `modules/auth_saml/{controllers/providers_controller,views/providers/index}` |
| `ldap_groups` | `guard_enterprise_feature`, disabled buttons, job early-return, user-limit stop | `modules/ldap_groups/**`, `modules/ldap_departments/**` (controllers, components, views, `*synchronization_job.rb`, `synchronize_*_service.rb`) |
| `meeting_templates` | contract-like checks in controllers, menu icon, banner | `modules/meeting/app/{components,controllers,menus,views}/**` |
| `resource_management` | `ensure_resource_management_licensed`, project module `enterprise_feature`, banners | `modules/resource_management/**` |
| `team_planner_view` | `guard_enterprise_feature`, `upsell` action/permissions, module metadata | `modules/team_planner/**` |
| `time_entry_time_restrictions` | `TimeEntry` limits + disabled settings, banner | `modules/costs/app/models/time_entry.rb`, `modules/costs/app/views/admin/time_settings/show.html.erb` |
| `nextcloud_sso`, `one_drive_sharepoint_file_storage` | storage contracts, `allowed_by_enterprise_token?` on models, `upsell` page/route, API 500 | `modules/storages/**` (contracts, models, controller, forms, components, routes, API, `storage_error_helper.rb`), `frontend/.../storage.component.ts`, `frontend/.../error-resource.ts` |
| `xwiki_integration` | `ee_token_allows_wiki_integration` before_action, banner | `modules/wikis/**` |
| `sprint_sharing`, `multiple_active_sprints` | contract validations, banners, `only_fallback_allowed`, copy-service cleanup | `modules/backlogs/**` |
| user limit (`user_limit`) | `UserLimits` concern, contracts, API, mails, banner | A-C3 + `app/controllers/{account,users}_controller.rb`, `app/controllers/concerns/member_helper.rb`, `app/contracts/users/*`, `lib/api/v3/users/users_api.rb`, `app/components/{shares/invite_user_form,users/index_page_header}_component.*`, `app/views/members/_member_form.html.erb` (seats = `999999`), `modules/bim/.../bcf_xml/importer.rb`, `modules/ldap_*/**` |
| Upsell chrome | trial teaser, "upgrade" buttons, enterprise menu, help-menu links, homescreen upsell block, security badge `ee:` flag | `app/views/layouts/base.html.erb`, `config/initializers/{menus,homescreen}.rb`, `lib/redmine/menu_manager/**`, `app/helpers/{homescreen,security_badge}_helper.rb`, `config/static_links.yml` (upsell/pricing/enterprise_guide links removed), `app/components/open_project/common/submenu_component.html.erb` |

### 1.3 Findings: resolved and still open

Resolved on 2026-10-15 (each one is also an invariant in `invariants.tsv`):

| ID | Where | Fix |
|----|-------|-----|
| F-1 | `frontend/.../onboarding/onboarding_tour.ts` | `showTeamPlannerTour()` no longer reads `configuration.availableFeatures`; the tour depends only on the demo data and module visibility |
| F-2 | `app/views/custom_fields/_tab.html.erb` | leftover `custom_field_hierarchies` banner render removed |
| F-3 | `app/views/admin/settings/authentication_settings/_sso.html.erb` | "password login requires an SSO provider" warning restored (it is plain UI, not an EE banner) |
| F-4 | `modules/wikis/app/views/wikis/admin/wiki_providers/index.html.erb` | provider list rendered unconditionally |
| F-6 | `user-autocompleter-template.component.ts` | stray leading space removed |
| F-10 | `app/helpers/projects_helper.rb` | `portfolio_management_feature_missing?` returns `false`, so `layout_for_new` keeps `"no_menu"` for portfolios/programs |
| - | `custom_scripts/sync_upstream` | usage text now says `custom_scripts/sync_upstream` |

Open / accepted:

| ID | Where | Note |
|----|-------|------|
| F-5 | `config/initializers/appsignal.rb` | `Appsignal.start` is removed on purpose (no telemetry). Keep. |
| F-7 | 3 spec fixtures (`spec/fixtures/files/testfile-utf8.txt`, `modules/bim/spec/fixtures/files/minimal.ifc`, `modules/documents/spec/assets/attachments/testfile.txt`) | Line-ending noise. **Policy: spec files are never modified or restored**; leave as is. |
| F-8 | `spec/**` | Specs are not run and never adapted to the fork. Ignore their EE assertions. |
| F-9 | `app/views/enterprise_tokens/*`, `/enterprise_tokens` | Page still reachable by URL for admins. Harmless. |

---

## 2. Category B - Local bug fixes and behavioural patches (not EE-related)

| ID | File | Marker | What & why | On merge |
|----|------|--------|------------|----------|
| B-1 | `app/mailers/user_mailer.rb` (2 places: `news_added`, `news_comment_added`) | `OP-CUSTOM` | Adds the missing leading `[` to project-prefixed news mail subjects (`[Project] News: Title`) | If upstream fixes it, drop ours |
| B-2 | `modules/openid_connect/app/services/openid_connect/configuration_mapper.rb` | `CUSTOM CHANGE` | `sync_groups` is cast with `ActiveModel::Type::Boolean` (ENV values are already booleans, upstream compared with `"true"`) | Re-check upstream line `options["sync_groups"] == "true"` |
| B-3 | same file | `CUSTOM CHANGE` | Adds ENV mapping `group_prefixes` / `group_regexes` for ENV-seeded OIDC providers | Remove if upstream adds native support |
| B-4 | `modules/openid_connect/lib/open_project/openid_connect/hooks/hook.rb` (+ `spec/.../hook_spec.rb`) | `CUSTOM CHANGE` | Falls back to the ID token for the `groups` claim (Microsoft Entra ID never returns groups from UserInfo): `extract_groups_claim`, `id_token_claims` | Keep the call if upstream still digs `raw_info`; remove if upstream supports ID-token groups |

Tip: `custom_scripts/enterprise_audit.py markers` lists all marker comments.

## 3. Category C - Fork-only features and files (do not exist upstream)

| ID | Path | Description |
|----|------|-------------|
| C-1 | `modules/gitlab_integration/**` (extensions) | Upstream ships `gitlab_integration` (links GitLab issues/MRs to work packages). The fork adds: **GitLab configuration per project** (`GitlabConfiguration` model + migrations `20250126000001`, `20250211000001`, encrypted token, API `gitlab_configurations`, Angular `gitlab-setup`), **create merge request / issue from a work package** (services `create_merge_request.rb`, `create_issue.rb`, API endpoints, Angular `link-type-menu`, tab headers), `gitlab_author_name` columns, new permissions `manage_gitlab_configuration` and `delete_gitlab_links`, rake task `gitlab_integration.rake`, German locale entries, ~40 Markdown design notes in the module root and `doc/`. |
| C-2 | `modules/gitlab_integration/lib/open_project/gitlab_integration/notification_handler/merge_request_hook.rb` | **Hardcoded work package status ids** `483` ("In development") on new MR and `488` ("Merged"), `update_status_on_*` set to `true`. Environment specific - verify the ids still exist in the target database. |
| C-3 | `.../notification_handler/note_hook.rb` | Issue/snippet/MR **descriptions** are also scanned for `OP#123` references. |
| C-4 | `docker/prod/Dockerfile-slim` (+ `docker/prod/setup/preinstall-common.sh` keeps `curl`) | Slim production image built by CI (Ruby 4.0.6 / Debian trixie base args, `hocuspocus` image tag). **Version bumps follow upstream `docker/prod/Dockerfile`** - on each release diff the two and port base image / node / npm / hocuspocus changes (see commit "Update hocuspocus image to ..."). Only the `slim` target is active; `slim-bim` and `all-in-one` are commented out. |
| C-5 | `.gitlab-ci.yml` | Internal GitLab pipeline (stages ldap_sync, extract_version, build, publish, deploy_*), uses `custom_scripts/get_version.py` and `custom_scripts/ldap_sync.py`; only `develop` builds `openproject-slim`. Upstream's `.github/workflows` stay but are unused. |
| C-6 | `custom_scripts/*` | See [HUMAN_GUIDE.md §6](HUMAN_GUIDE.md#6-custom-scripts-custom_scripts). |
| C-7 | `custom_maintenance/**`, `.claude/skills/openproject-ee-unlock-maintenance/` | This maintenance kit. |

## 4. Changes that upstream carries that the fork must NOT revert

When resolving conflicts, **take upstream** for everything except the files and hunks listed in §1-§3. Typical
traps: `Gemfile.lock`, `config/locales/**` (Crowdin), `docs/**`, `frontend/package*.json`, `.ruby-version`,
`docker/prod/Dockerfile` (upstream version, then re-port to `Dockerfile-slim`), `publiccode.yml`,
`docs/release-notes/**`. `frontend/package-lock.json` is git-ignored.
