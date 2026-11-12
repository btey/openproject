# Hide Create Buttons When GitLab Not Configured

## The Problem

When viewing a project that doesn't have GitLab configured (empty GitLab URL, Project Identifier, or Access Token), the Create Issue and Create MR buttons (along with their checkboxes) were still visible. This was confusing because clicking them would fail.

## The Solution

Added **configuration checks** to both Issue and MR header components that:
1. Check if GitLab is configured for the project on component initialization
2. Hide the Create buttons and checkboxes when GitLab is not configured
3. Keep the "Git snippets" button visible (it doesn't require GitLab configuration)

## Implementation

### Configuration Check Logic

Both components now check if GitLab is configured by:
1. Fetching the GitLab configuration from the API
2. Checking if all three required fields are present:
   - `gitlabUrl` (not null/empty)
   - `projectIdentifier` (not null/empty)
   - `accessTokenPresent` (true)

```typescript
checkGitlabConfiguration():void {
  const projectId = this.workPackage.project.id;
  const apiUrl = `${this.pathHelper.api.v3.apiV3Base}/projects/${projectId}/gitlab_configuration`;

  this.http.get<any>(apiUrl).subscribe({
    next: (config) => {
      // Check if GitLab is configured (has URL, project identifier, and access token)
      this.isGitlabConfigured = !!(
        config.gitlabUrl && 
        config.projectIdentifier && 
        config.accessTokenPresent
      );
    },
    error: () => {
      this.isGitlabConfigured = false;
    }
  });
}
```

### Template Changes

Added `*ngIf="isGitlabConfigured"` to conditionally render the buttons:

**Issues Section:**
```html
<ul class="toolbar-items hide-when-print" *ngIf="isGitlabConfigured">
  <!-- Checkbox and Create Issue button only show when configured -->
</ul>
```

**Merge Requests Section:**
```html
<li class="toolbar-item" *ngIf="isGitlabConfigured">
  <!-- Checkbox -->
</li>
<li class="toolbar-item" *ngIf="isGitlabConfigured">
  <!-- Create MR button -->
</li>
<li class="toolbar-item">
  <!-- Git snippets button - ALWAYS visible -->
</li>
```

## Files Modified

### Components
- ✅ `frontend/module/tab-header-issue/tab-header-issue.component.ts`
  - Added `OnInit` interface
  - Added `isGitlabConfigured` property
  - Added `HttpClient` and `PathHelperService` dependencies
  - Added `ngOnInit()` and `checkGitlabConfiguration()` methods

- ✅ `frontend/module/tab-header-mr/tab-header-mr.component.ts`
  - Added `OnInit` interface
  - Added `isGitlabConfigured` property
  - Added `HttpClient` and `PathHelperService` dependencies
  - Added `ngOnInit()` and `checkGitlabConfiguration()` methods

### Templates
- ✅ `frontend/module/tab-header-issue/tab-header-issue.template.html`
  - Added `*ngIf="isGitlabConfigured"` to toolbar items

- ✅ `frontend/module/tab-header-mr/tab-header-mr.template.html`
  - Added `*ngIf="isGitlabConfigured"` to checkbox and Create MR button
  - Git snippets button remains always visible

## Behavior

### When GitLab IS Configured
```
Issues
  ☐ Private link (PP#)  [+ Create Issue]
  ↑                     ↑
  Visible              Visible

Merge Requests
  ☐ Private link (PP#)  [+ Create MR]  [...Git snippets]
  ↑                     ↑                ↑
  Visible              Visible          Visible
```

### When GitLab NOT Configured
```
Issues
  (empty - no buttons)

Merge Requests
  [...Git snippets]
  ↑
  Only this button visible
```

## Configuration Requirements

For buttons to appear, the project must have:
1. ✅ **GitLab URL** - Not empty (e.g., `https://gitlab.com`)
2. ✅ **Project Identifier** - Not empty (e.g., `mygroup/myproject`)
3. ✅ **Access Token** - Present (doesn't need to be valid, just present)

If **any** of these is missing, the Create buttons and checkboxes are hidden.

## Why Git Snippets Button Stays Visible

The "Git snippets" button (copy branch name, commit message, etc.) doesn't require GitLab API access. It just generates text based on the work package data, so it remains visible even when GitLab is not configured.

## User Experience

### Scenario 1: New Project (No GitLab)
User opens GitLab tab → Only sees:
- Issues title (empty list or existing linked issues)
- Merge Requests title + Git snippets button (empty list or existing linked MRs)
- **No Create buttons visible** ✅

User must configure GitLab via "GitLab Setup" first.

### Scenario 2: Configured Project
User opens GitLab tab → Sees:
- Issues title + checkbox + Create Issue button
- Merge Requests title + checkbox + Create MR button + Git snippets button
- **All buttons visible** ✅

### Scenario 3: Partially Configured
If user fills in URL but not project identifier:
- **Create buttons hidden** ✅
- User must complete configuration

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Test Unconfigured Project:**
- Go to a work package in a project **without** GitLab configured
- Open GitLab tab
- **Expected**: No Create buttons or checkboxes visible
- **Expected**: Git snippets button still visible

**3. Test Configured Project:**
- Go to GitLab Setup, configure GitLab
- Save configuration
- Refresh page
- **Expected**: Create buttons and checkboxes now visible

**4. Test Partial Configuration:**
- Go to GitLab Setup
- Fill in only GitLab URL (leave project identifier empty)
- Save
- Refresh page
- **Expected**: Create buttons still hidden (needs all fields)

## API Call

The configuration check makes a GET request on component initialization:
```
GET /api/v3/projects/:id/gitlab_configuration
```

Response is checked for:
```typescript
{
  gitlabUrl: "https://gitlab.com",        // Must be present
  projectIdentifier: "mygroup/myproject", // Must be present
  accessTokenPresent: true                // Must be true
}
```

If any field is missing/null/false, buttons are hidden.

## Performance

- ✅ Single API call per component on initialization
- ✅ No polling or repeated checks
- ✅ Cached in component state (`isGitlabConfigured`)
- ✅ Lightweight check (just boolean evaluation)

## Summary

🎯 **Create Issue and Create MR buttons (and their checkboxes) now intelligently hide when GitLab is not configured!**

This prevents user confusion and failed operations. Users must configure GitLab via "GitLab Setup" before these buttons appear.

**Git snippets button remains visible** as it doesn't require GitLab API access.

Just **restart your server** with `bin/dev` and test with both configured and unconfigured projects! 🚀

