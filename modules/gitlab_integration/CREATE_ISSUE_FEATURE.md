# Create Issue Feature - Implementation Summary

## Overview

Added a "Create Issue" button to the GitLab Issues section header, similar to the existing "Create MR" button in the Merge Requests section.

## What Was Implemented

### Backend (Ruby/Rails)

1. **Service Class**: `lib/open_project/gitlab_integration/services/create_issue.rb`
   - Creates a new GitLab issue via GitLab API
   - Uses the project's GitLab configuration (URL, project identifier, access token)
   - Formats the issue with:
     - Title: `OP#<work_package_id>: <work_package_subject>`
     - Description: Work package details and description (truncated to 500 chars)

2. **API Endpoint**: `lib/api/v3/gitlab_issues/create_gitlab_issue_api.rb`
   - POST endpoint: `/api/v3/work_packages/:id/create_gitlab_issue`
   - Requires `show_gitlab_content` permission
   - Returns 201 status with GitLab issue data on success

3. **Engine Configuration**: Updated `lib/open_project/gitlab_integration/engine.rb`
   - Added API path: `create_gitlab_issue`
   - Mounted the API endpoint

### Frontend (Angular/TypeScript)

1. **Service**: `frontend/module/gitlab-issue.service.ts`
   - Angular service to call the Create Issue API endpoint
   - Registered as singleton service (`providedIn: 'root'`)

2. **Component**: Updated `frontend/module/tab-header-issue/tab-header-issue.component.ts`
   - Added `isCreatingIssue` state flag
   - Added `createIssue()` method
   - Integrated with `GitlabIssueService`
   - Shows toast notifications on success/error
   - Opens created issue in new tab (if `web_url` returned)
   - Refreshes page after 1 second to show new issue in list

3. **Template**: Updated `frontend/module/tab-header-issue/tab-header-issue.template.html`
   - Added "Create Issue" button with icon
   - Button disables while creating (shows "Creating Issue...")
   - Positioned next to the "Issues" title

4. **Module**: Updated `frontend/module/main.ts`
   - Imported `GitlabIssueService` and `GitlabMergeRequestService`
   - Added both services to providers list

5. **Translations**: Updated `config/locales/js-en.yml`
   - Added translations for:
     - Button label: "Create Issue"
     - Button description
     - Loading state: "Creating Issue..."
     - Success message
     - Error message

## How It Works

### User Flow

1. User opens a work package → GitLab tab
2. Scrolls to the "Issues" section
3. Clicks the **"Create Issue"** button next to the section title
4. Button shows "Creating Issue..." and is disabled
5. API creates a new issue in GitLab with:
   - Title: `OP#123: Work Package Title`
   - Description: Work package details
6. Success:
   - Toast notification: "Issue created successfully!"
   - Issue opens in new browser tab
   - Page refreshes after 1s to show the new issue
7. Error:
   - Toast notification with error message
   - Button re-enables

### API Call Flow

```
Frontend (Angular)
    ↓
GitlabIssueService.createIssue(workPackageId)
    ↓
POST /api/v3/work_packages/:id/create_gitlab_issue
    ↓
CreateGitlabIssueAPI (Authorization check)
    ↓
CreateIssue Service
    ↓
GitLab API: POST /api/v4/projects/:id/issues
    ↓
Response with issue data (including web_url)
    ↓
Frontend displays success + opens issue
```

## Files Created

### Backend
- `/modules/gitlab_integration/lib/open_project/gitlab_integration/services/create_issue.rb`
- `/modules/gitlab_integration/lib/api/v3/gitlab_issues/create_gitlab_issue_api.rb`

### Frontend
- `/modules/gitlab_integration/frontend/module/gitlab-issue.service.ts`

## Files Modified

### Backend
- `/modules/gitlab_integration/lib/open_project/gitlab_integration/engine.rb`
  - Added `create_gitlab_issue` API path
  - Mounted `CreateGitlabIssueAPI` endpoint

### Frontend
- `/modules/gitlab_integration/frontend/module/tab-header-issue/tab-header-issue.component.ts`
  - Added Create Issue functionality
  - Integrated services and toast notifications

- `/modules/gitlab_integration/frontend/module/tab-header-issue/tab-header-issue.template.html`
  - Added Create Issue button with icon

- `/modules/gitlab_integration/frontend/module/main.ts`
  - Imported and registered new services

### Translations
- `/modules/gitlab_integration/config/locales/js-en.yml`
  - Added Create Issue translations

## Requirements

- GitLab must be configured for the project (via GitLab Setup)
- User must have `show_gitlab_content` permission
- Valid GitLab URL, project identifier, and access token required

## Button Location

The "Create Issue" button appears in the **Issues section header**, positioned:
- Next to the "Issues" title (h3)
- Before the issue list
- Same design/layout as "Create MR" button in Merge Requests section

## Testing

### To Test the Feature:

1. **Restart Rails server** to load new backend code:
   ```bash
   bin/dev
   ```

2. **Ensure GitLab is configured**:
   - Go to GitLab tab
   - Click "GitLab Setup"
   - Fill in URL, project identifier, and access token
   - Save

3. **Test Create Issue**:
   - Open any work package
   - Go to GitLab tab
   - Scroll to "Issues" section
   - Click "Create Issue" button
   - Verify:
     - Button shows "Creating Issue..."
     - Success toast appears
     - Issue opens in new tab
     - Page refreshes and shows new issue

### Expected Results

✅ Button appears next to "Issues" title
✅ Button shows loading state while creating
✅ Success notification appears
✅ Issue created in GitLab with correct title/description
✅ Issue opens in new browser tab
✅ New issue appears in the list after refresh

### Error Cases

❌ **No GitLab configuration**: "GitLab not configured for this project"
❌ **Invalid credentials**: "Failed to create issue: 401 Unauthorized"
❌ **Network error**: "Failed to create issue: <error message>"
❌ **Invalid project**: "Failed to create issue: 404 Not Found"

## Similar to Create MR

This feature follows the exact same pattern as the existing "Create MR" feature:

| Aspect | Create MR | Create Issue |
|--------|-----------|--------------|
| Service | `CreateMergeRequest` | `CreateIssue` |
| API Endpoint | `CreateGitlabMergeRequestAPI` | `CreateGitlabIssueAPI` |
| Frontend Service | `GitlabMergeRequestService` | `GitlabIssueService` |
| Component | `TabHeaderMrsComponent` | `TabHeaderIssueComponent` |
| Button Label | "Create MR" | "Create Issue" |
| Loading Text | "Creating Merge Request..." | "Creating Issue..." |

## Security

- Uses the same permission as viewing GitLab content: `show_gitlab_content`
- Access token is stored securely in `gitlab_configurations` table
- API calls are made server-side (token never exposed to frontend)

## Future Enhancements

Possible improvements:
1. Allow customizing issue labels/assignees
2. Add milestone selection
3. Support issue templates
4. Add confidential issue option
5. Allow selecting issue type

## Deployment Notes

After deploying:
1. ✅ Restart Rails server
2. ✅ Frontend will automatically pick up changes (or rebuild: `npm run build`)
3. ✅ No database migrations required
4. ✅ No new permissions to assign (uses existing `show_gitlab_content`)

## Summary

The Create Issue feature is now fully implemented and matches the Create MR functionality. Users can create GitLab issues directly from OpenProject work packages with a single click!

**Button Location**: Issues section header, next to the "Issues" title ✅

