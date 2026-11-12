# Private Link (PP#) Feature - Implementation Summary

## Overview

Added the ability for users to choose between **OP# (public/open)** and **PP# (private)** prefixes when creating GitLab Issues and Merge Requests.

## The Problem

Previously, all created Issues and MRs used the "OP#" prefix (e.g., `OP#123: Work Package Title`). However, GitLab integration supports two types of links:
- **OP#** - Public/Open project links
- **PP#** - Private project links

Users needed a way to choose which prefix to use when creating Issues/MRs.

## The Solution: Checkbox

I implemented a **checkbox** next to each Create button that allows users to choose on-the-fly:

```
[ ] Private link (PP#)  [Create Issue]
```

- **Unchecked (default)**: Uses `OP#123`
- **Checked**: Uses `PP#123`

## Implementation Details

### Backend Changes

#### 1. Services Updated
Both `CreateIssue` and `CreateMergeRequest` services now accept a `private_link` parameter:

**Before:**
```ruby
def initialize(work_package:, user:)
  @work_package = work_package
  @user = user
end

def issue_title
  "OP##{work_package.id}: #{work_package.subject}"
end
```

**After:**
```ruby
def initialize(work_package:, user:, private_link: false)
  @work_package = work_package
  @user = user
  @private_link = private_link
end

def issue_title
  "#{prefix}##{work_package.id}: #{work_package.subject}"
end

def prefix
  private_link ? "PP" : "OP"
end
```

#### 2. API Endpoints Updated
Both API endpoints now accept and pass through the `private_link` parameter:

```ruby
post do
  authorize_in_work_package(:show_gitlab_content, work_package: @work_package)
  
  private_link = params[:private_link] == true || params[:private_link] == "true"
  
  result = ::OpenProject::GitlabIntegration::Services::CreateIssue
            .new(work_package: @work_package, user: current_user, private_link:)
            .call
  # ...
end
```

### Frontend Changes

#### 1. Services Updated
Angular services now accept the `privateLink` parameter:

```typescript
public createIssue(workPackageId:string, privateLink:boolean = false):Observable<any> {
  const url = `/api/v3/work_packages/${workPackageId}/create_gitlab_issue`;
  return this.http.post(url, { private_link: privateLink });
}
```

#### 2. Components Updated
Both header components track checkbox state and pass it to the service:

```typescript
export class TabHeaderIssueComponent {
  public isCreatingIssue = false;
  public usePrivateLink = false; // ← New state

  public createIssue():void {
    this.gitlabIssueService.createIssue(this.workPackage.id!, this.usePrivateLink)
      .subscribe({ /* ... */ });
  }
}
```

#### 3. Templates Updated
Added checkbox before the Create button:

```html
<ul class="toolbar-items hide-when-print">
  <li class="toolbar-item">
    <label class="checkbox-label">
      <input
        type="checkbox"
        [(ngModel)]="usePrivateLink"
        [disabled]="isCreatingIssue"
      />
      <span class="checkbox-text">{{text.privateLink}}</span>
    </label>
  </li>
  <li class="toolbar-item">
    <button class="button" (click)="createIssue()">
      <!-- Create Issue button -->
    </button>
  </li>
</ul>
```

#### 4. Styling Added
Added checkbox styling to both header sass files:

```sass
.checkbox-label
  display: flex
  align-items: center
  gap: 0.5rem
  cursor: pointer
  
  input[type="checkbox"]
    cursor: pointer
    
  .checkbox-text
    font-size: 0.875rem
    white-space: nowrap
```

#### 5. Translations Added
Added i18n keys for both sections:

```yaml
private_link: "Private link (PP#)"
private_link_description: "Use PP# prefix instead of OP# for private project links"
```

## Files Modified

### Backend
- ✅ `lib/open_project/gitlab_integration/services/create_issue.rb`
- ✅ `lib/open_project/gitlab_integration/services/create_merge_request.rb`
- ✅ `lib/api/v3/gitlab_issues/create_gitlab_issue_api.rb`
- ✅ `lib/api/v3/gitlab_merge_requests/create_gitlab_merge_request_api.rb`

### Frontend
- ✅ `frontend/module/gitlab-issue.service.ts`
- ✅ `frontend/module/gitlab-merge-request.service.ts`
- ✅ `frontend/module/tab-header-issue/tab-header-issue.component.ts`
- ✅ `frontend/module/tab-header-issue/tab-header-issue.template.html`
- ✅ `frontend/module/tab-header-issue/styles/tab-header-issue.sass`
- ✅ `frontend/module/tab-header-mr/tab-header-mr.component.ts`
- ✅ `frontend/module/tab-header-mr/tab-header-mr.template.html`
- ✅ `frontend/module/tab-header-mr/styles/tab-header-mr.sass`

### Translations
- ✅ `config/locales/js-en.yml`

## User Experience

### Before
```
Issues
  [Create Issue] ← Creates "OP#123: Title"
```

### After
```
Issues
  [ ] Private link (PP#)  [Create Issue]
  ↑                       ↑
  Check to use PP#        Creates OP#123 or PP#123
```

### Usage Flow

1. **Default (Unchecked)**: Creates issue with `OP#123: Work Package Title`
2. **Checked**: Creates issue with `PP#123: Work Package Title`
3. Checkbox state is independent - user can check/uncheck for each creation
4. Checkbox is disabled while creating (prevents changes mid-creation)

## Benefits of Checkbox Approach

### ✅ Pros
1. **Flexible**: Choose per action, not a global setting
2. **Visible**: Clear what the checkbox does
3. **Simple**: No extra clicks or dropdowns
4. **Accessible**: Proper ARIA labels and disabled states
5. **Intuitive**: Checkbox metaphor matches binary choice
6. **Consistent**: Same pattern for both Issues and MRs

### Alternative Approaches Considered

#### Option 2: Split Button Dropdown
```
[Create Issue ▼]
  ├─ Create with OP#
  └─ Create with PP#
```
- ❌ More clicks required
- ❌ More complex to implement
- ✅ Cleaner UI (takes less space)

#### Option 3: Global Setting
Add preference in GitLab Setup form
- ❌ Less flexible (one setting for all)
- ❌ Users might forget the setting
- ✅ Simpler UI (no extra controls per section)

**Checkbox was chosen as the best balance of flexibility and usability.**

## Testing

### To Test:

1. **Restart Rails server**: `bin/dev`

2. **Test Create Issue with OP#**:
   - Go to GitLab tab → Issues section
   - Leave checkbox **unchecked**
   - Click "Create Issue"
   - Verify issue created with title: `OP#123: ...`

3. **Test Create Issue with PP#**:
   - **Check** the "Private link (PP#)" checkbox
   - Click "Create Issue"
   - Verify issue created with title: `PP#123: ...`

4. **Test Create MR with OP#**:
   - Go to Merge Requests section
   - Leave checkbox **unchecked**
   - Click "Create MR"
   - Verify MR created with title: `OP#123: ...`

5. **Test Create MR with PP#**:
   - **Check** the "Private link (PP#)" checkbox
   - Click "Create MR"
   - Verify MR created with title: `PP#123: ...`

### Expected Behavior

✅ Checkbox appears next to Create buttons
✅ Checkbox labeled "Private link (PP#)"
✅ Tooltip explains the purpose
✅ Unchecked (default) creates with OP# prefix
✅ Checked creates with PP# prefix
✅ Checkbox disabled while creating
✅ Checkbox state is independent (per section)
✅ Title and description use correct prefix

## Visual Layout

```
┌─────────────────────────────────────────────┐
│ 📋 Issues                                   │
│    [ ] Private link (PP#)  [+ Create Issue]│
│    ↑                        ↑               │
│    Checkbox                 Button          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🔀 Merge Requests                           │
│    [ ] Private link (PP#)  [+ Create MR]   │
│                            [...Git snippets]│
└─────────────────────────────────────────────┘
```

## API Request Examples

### Create Issue with OP# (default)
```bash
POST /api/v3/work_packages/123/create_gitlab_issue
{
  "private_link": false  # or omitted
}
```
**Result**: `OP#123: Work Package Title`

### Create Issue with PP#
```bash
POST /api/v3/work_packages/123/create_gitlab_issue
{
  "private_link": true
}
```
**Result**: `PP#123: Work Package Title`

## Backward Compatibility

✅ **Fully backward compatible**:
- If `private_link` parameter is omitted, defaults to `false` (OP# prefix)
- Existing API calls continue to work without changes
- Default behavior unchanged (OP# prefix)

## Summary

🎉 **Users can now choose between OP# and PP# prefixes when creating GitLab Issues and Merge Requests!**

The checkbox provides a flexible, intuitive way to select the prefix type without requiring configuration changes or extra navigation.

**Simple to use:**
1. Checkbox unchecked (default) = OP#
2. Checkbox checked = PP#
3. Click Create button
4. Done!

