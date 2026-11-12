# ✅ Create Issue Feature - Ready to Test!

## What Was Done

I've successfully implemented a "Create Issue" button next to the "Issues" title in the GitLab tab, matching the existing "Create MR" functionality.

## Files Created/Modified

### ✅ Backend Files Created
1. **Service**: `lib/open_project/gitlab_integration/services/create_issue.rb`
   - Creates issues in GitLab via API
   
2. **API Endpoint**: `lib/api/v3/gitlab_issues/create_gitlab_issue_api.rb`
   - POST endpoint for creating issues

### ✅ Frontend Files Created
3. **Service**: `frontend/module/gitlab-issue.service.ts`
   - Angular service to call the API

### ✅ Backend Files Modified
4. **Engine**: `lib/open_project/gitlab_integration/engine.rb`
   - Registered API path and endpoint

### ✅ Frontend Files Modified
5. **Component**: `frontend/module/tab-header-issue/tab-header-issue.component.ts`
   - Added Create Issue button logic
   
6. **Template**: `frontend/module/tab-header-issue/tab-header-issue.template.html`
   - Added Create Issue button HTML

7. **Module**: `frontend/module/main.ts`
   - Registered the new service

### ✅ Translations
8. **i18n**: `config/locales/js-en.yml`
   - Added Create Issue translations

## What to Do Now

### 1. Restart Rails Server (REQUIRED!)

```bash
# Stop your server (Ctrl+C)
# Then restart:
bin/dev
```

### 2. Test the Feature

1. **Open a work package** in a project with GitLab enabled
2. **Go to the GitLab tab**
3. **Scroll to the "Issues" section**
4. **You should see** a "Create Issue" button next to the "Issues" title
5. **Click the button**
6. **Expected behavior**:
   - Button shows "Creating Issue..."
   - Success notification appears
   - Issue opens in new GitLab tab
   - Page refreshes to show the new issue

## Button Location

```
GitLab Tab
  ├─ GitLab Setup (collapsible section)
  │
  ├─ Issues ← "Create Issue" button is here!
  │   ├─ [Create Issue] button
  │   └─ List of issues...
  │
  └─ Merge Requests
      ├─ [Create MR] button
      └─ List of MRs...
```

## How It Works

**When you click "Create Issue":**

1. Sends POST request to: `/api/v3/work_packages/:id/create_gitlab_issue`
2. Backend creates issue in GitLab with:
   - **Title**: `OP#<id>: <work package subject>`
   - **Description**: Work package details
3. Returns the created issue data
4. Opens the issue in a new browser tab
5. Refreshes the page to show the new issue in the list

## Requirements

Before using:
- ✅ GitLab must be configured (click "GitLab Setup" and fill in details)
- ✅ Valid GitLab URL, project identifier, and access token
- ✅ User has `show_gitlab_content` permission

## Matching Create MR

The Create Issue feature works **exactly like Create MR**:

| Feature | Create MR | Create Issue |
|---------|-----------|--------------|
| Button Location | Next to "Merge Requests" title | Next to "Issues" title |
| Button Label | "Create MR" | "Create Issue" |
| Loading State | "Creating Merge Request..." | "Creating Issue..." |
| Success Message | "Merge Request created successfully!" | "Issue created successfully!" |
| Opens in New Tab | ✅ Yes | ✅ Yes |
| Refreshes List | ✅ Yes | ✅ Yes |

## Visual Design

The button has:
- ✅ Plus (+) icon
- ✅ "Create Issue" text
- ✅ Disabled state while creating
- ✅ Loading text: "Creating Issue..."
- ✅ Proper ARIA labels for accessibility

## Error Handling

If something goes wrong, you'll see a toast notification with:
- ❌ "GitLab not configured for this project" (if no config)
- ❌ "Failed to create Issue: 401 Unauthorized" (if bad token)
- ❌ "Failed to create Issue: <error>" (other errors)

## Testing Checklist

After restarting the server, verify:

- [ ] GitLab tab loads without errors
- [ ] "Create Issue" button appears next to "Issues" title
- [ ] Button has a plus (+) icon
- [ ] Clicking button shows "Creating Issue..."
- [ ] Button is disabled while creating
- [ ] Success toast notification appears
- [ ] Issue opens in new GitLab tab
- [ ] Created issue has correct title: `OP#<id>: <subject>`
- [ ] Page refreshes and new issue appears in list
- [ ] Error handling works (test with invalid config)

## Documentation

Full details in: `CREATE_ISSUE_FEATURE.md`

## Summary

🎉 **The Create Issue feature is complete and ready to use!**

Just **restart your Rails server** with `bin/dev` and you'll see the new "Create Issue" button next to the "Issues" title in the GitLab tab.

The button works exactly like "Create MR" - click it, and it creates a new issue in GitLab with your work package details, then opens it in a new tab!

