# ✅ Added Horizontal Line Separator to Issue/MR Descriptions

## What Was Added

Added a **horizontal line separator (`---`)** between the OpenProject reference header and the work package description in GitLab Issues and Merge Requests.

## Visual Change

### Before (No Separator)

```
This issue is related to OpenProject work package OP#123

**Work Package:** Task Title

This is the work package description...
```

### After (With Separator)

```
This issue is related to OpenProject work package OP#123

**Work Package:** Task Title

---

This is the work package description...
```

## Why This is Better

✅ **Visual Clarity** - Clear separation between metadata and content
✅ **Professional Look** - Follows markdown documentation conventions
✅ **Easy to Read** - Immediately see where work package content starts
✅ **Better Scanning** - Users can quickly skip to the actual description

## Implementation

### Markdown Syntax

The horizontal line uses markdown syntax:
```markdown
---
```

This renders as a horizontal rule (line) in GitLab's markdown renderer.

### Both Services Updated

**Create Issue Service:**
```ruby
def issue_description
  <<~DESC
    This issue is related to OpenProject work package #{prefix}##{work_package.id}

    **Work Package:** #{work_package.subject}

    ---

    #{work_package.description}
  DESC
end
```

**Create Merge Request Service:**
```ruby
def merge_request_description
  <<~DESC
    This merge request is related to OpenProject work package #{prefix}##{work_package.id}

    **Work Package:** #{work_package.subject}

    ---

    #{work_package.description}
  DESC
end
```

## Files Modified

- ✅ `lib/open_project/gitlab_integration/services/create_issue.rb` - Added `---` separator
- ✅ `lib/open_project/gitlab_integration/services/create_merge_request.rb` - Added `---` separator
- ✅ `REMOVE_DESCRIPTION_TRUNCATION.md` - Updated documentation

## Example Output

### Issue in GitLab

```markdown
This issue is related to OpenProject work package OP#123

**Work Package:** Implement User Authentication

---

## Overview
This task involves implementing user authentication for the application.

## Requirements
- OAuth2 support
- JWT tokens
- Password hashing with bcrypt

## Acceptance Criteria
1. Users can register
2. Users can login
3. Tokens expire after 24h
```

The `---` renders as a horizontal line, creating clear visual separation.

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Create Issue or MR:**
1. Create a work package with description
2. Click "Create Issue" or "Create MR"
3. Open in GitLab
4. **Verify**: Horizontal line appears between header and description ✅

### Expected Result

In GitLab, you'll see:
```
Reference info...
────────────────  ← Horizontal line
Work package description...
```

## Benefits

✅ **Professional Formatting** - Follows markdown best practices
✅ **Clear Separation** - Easy to distinguish metadata from content
✅ **Better UX** - Users can quickly scan and find content
✅ **Consistent Style** - Same separator in both Issues and MRs

## Summary

Added a horizontal line (`---`) separator between the OpenProject reference header and the work package description to improve visual clarity and readability in GitLab Issues and Merge Requests.

Just **restart your server** with `bin/dev` and the next Issues/MRs you create will have the nice visual separator! 🎯

