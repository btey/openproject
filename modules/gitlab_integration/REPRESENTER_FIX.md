# GitLab Configuration - Representer and Permission Fixes

## Issues

### Issue 1: Representer Error
Error when accessing the GitLab tab:
```
ERROR -- : undefined local variable or method 'represented' for an instance of GitlabConfiguration
```

### Issue 2: GitLab Setup Button Not Visible
The "GitLab Setup" button was not visible even for users with the "Manage GitLab Configuration" permission checked.

## Root Causes

### Representer Issue
The `GitlabConfigurationRepresenter` was using incorrect syntax for defining the `access_token_present` property. The original code used:

```ruby
property :access_token_present,
         getter: ->(*) { represented.access_token.present? },
         render_nil: true
```

The problem is that within a lambda/proc passed to `getter:`, the context is not the decorator instance, so `represented` is not available.

### Permission Issue
The `manage_gitlab_configuration` permission was only set to be permissible on `:project` context:

```ruby
permission(:manage_gitlab_configuration,
           {},
           permissible_on: :project,
           dependencies: :show_gitlab_content)
```

Since the GitLab tab is accessed from a work package view, the permission needs to be available on both `work_package` and `project` contexts.

Additionally, the frontend had no way to check if the user had this permission, so it defaulted to checking for project `update` link.

## Solutions

### Representer Fix
Changed to use `exec_context: :decorator` which sets the execution context to the decorator instance, allowing us to define a proper method:

```ruby
property :access_token_present,
         exec_context: :decorator,
         render_nil: true

def access_token_present
  represented.access_token.present?
end
```

This pattern is used throughout OpenProject's API representers (see `API::V3::Users::UserRepresenter`, `API::V3::Errors::ErrorRepresenter`, etc.).

### Permission Fixes

1. **Updated permission context** in `engine.rb`:
```ruby
permission(:manage_gitlab_configuration,
           {},
           permissible_on: %i[work_package project],  # Added work_package
           dependencies: :show_gitlab_content)
```

2. **Added HAL link** in work package representer to expose the permission:
```ruby
link :manageGitlabConfiguration,
     cache_if: -> { current_user.allowed_in_work_package?(:manage_gitlab_configuration, represented) } do
  next if represented.new_record?

  {
    href: api_v3_paths.gitlab_configuration_by_project(represented.project.id),
    title: "Manage GitLab Configuration"
  }
end
```

3. **Updated frontend** to check for the HAL link:
```typescript
checkPermissions():void {
  // Check if user has the manage_gitlab_configuration permission
  // This is exposed via a HAL link on the work package resource
  this.canManage = !!(this.workPackage.manageGitlabConfiguration);
}
```

## Changes Made

1. **Fixed**: `lib/api/v3/gitlab_configurations/gitlab_configuration_representer.rb`
   - Removed the lambda-based `getter:`
   - Added `exec_context: :decorator`
   - Defined `access_token_present` as a method
   - Removed `self_link` (not needed for this resource)

2. **Fixed**: `lib/open_project/gitlab_integration/engine.rb`
   - Changed `permissible_on` from `:project` to `%i[work_package project]`

3. **Fixed**: `lib/open_project/gitlab_integration/patches/api/work_package_representer.rb`
   - Added `manageGitlabConfiguration` HAL link to expose permission to frontend

4. **Fixed**: `frontend/module/gitlab-setup/gitlab-setup.component.ts`
   - Updated permission check to look for `manageGitlabConfiguration` link

5. **Added**: `spec/lib/api/v3/gitlab_configurations/gitlab_configuration_representer_spec.rb`
   - Comprehensive tests for the representer
   - Tests for all properties including edge cases

## Testing

After these fixes:
1. **Restart your Rails server** to pick up the backend changes
2. **Rebuild frontend** if needed: `cd frontend && npm run build`
3. Access a work package in a project with GitLab module enabled
4. Go to the GitLab tab
5. If you have the "Manage GitLab Configuration" permission, you should now see the "GitLab Setup" button
6. Run tests: `bundle exec rspec modules/gitlab_integration/spec/lib/api/v3/gitlab_configurations/`

## How to Grant the Permission

As an administrator:
1. Go to **Administration** → **Roles and permissions**
2. Edit the role (e.g., "Project admin")
3. Under the **GitLab** section, check:
   - ✅ **Show GitLab content** (required to see the tab)
   - ✅ **Manage GitLab configuration** (required to see and use the setup form)
4. Save the role

The user needs to be assigned to this role in the project where they want to manage GitLab configuration.

## Additional Notes

- The `represented` method is provided by Roar and references the underlying model object
- Using `exec_context: :decorator` is the preferred pattern in OpenProject for custom property methods
- The representer correctly hides the actual `access_token` value for security
- Permissions in OpenProject can be context-specific (work_package, project, global)
- The GitLab tab is in a work package context, so permissions must be available there
- HAL links are the standard way to expose permissions to the frontend in OpenProject

