# Changed Issue/MR Title Format

## What Was Changed

Updated the title format for GitLab Issues and Merge Requests to put the OpenProject work package reference **at the end** instead of the beginning, using an em dash (—) as separator.

## Title Format Change

### Before

```
OP#123: Improve asset ingestion performance
```

Format: `{prefix}#{id}: {subject}`

### After

```
Improve asset ingestion performance — OP#123
```

Format: `{subject} — {prefix}#{id}`

## Why This is Better

✅ **Subject First** - The actual task/feature is immediately visible
✅ **Better Scanning** - Users see what it's about before the reference
✅ **Professional Look** - Matches common documentation styles
✅ **GitLab Lists** - Task names are more prominent in issue/MR lists
✅ **Search Friendly** - Subject keywords appear first

## Implementation

### Create Issue Service

**File**: `lib/open_project/gitlab_integration/services/create_issue.rb`

```ruby
# Before
def issue_title
  "#{prefix}##{work_package.id}: #{work_package.subject}"
end

# After
def issue_title
  "#{work_package.subject} — #{prefix}##{work_package.id}"
end
```

### Create Merge Request Service

**File**: `lib/open_project/gitlab_integration/services/create_merge_request.rb`

```ruby
# Before
def merge_request_title
  "#{prefix}##{work_package.id}: #{work_package.subject}"
end

# After
def merge_request_title
  "#{work_package.subject} — #{prefix}##{work_package.id}"
end
```

## Em Dash vs Hyphen

The separator uses an **em dash (—)** instead of a hyphen (-):
- Em dash: `—` (Unicode U+2014)
- Hyphen: `-`
- En dash: `–`

**Why em dash?**
- ✅ Professional typography
- ✅ Clear visual separation
- ✅ Commonly used in titles
- ✅ Distinguished from hyphens in compound words

## Files Modified

- ✅ `lib/open_project/gitlab_integration/services/create_issue.rb` - Updated title format
- ✅ `lib/open_project/gitlab_integration/services/create_merge_request.rb` - Updated title format

## Examples

### Example 1: Feature Task

**Work Package:**
- ID: 123
- Subject: "Implement user authentication"
- Prefix: OP

**Before:** `OP#123: Implement user authentication`
**After:** `Implement user authentication — OP#123`

### Example 2: Bug Fix

**Work Package:**
- ID: 456
- Subject: "Fix login page crash on mobile"
- Prefix: OP

**Before:** `OP#456: Fix login page crash on mobile`
**After:** `Fix login page crash on mobile — OP#456`

### Example 3: Private Link

**Work Package:**
- ID: 789
- Subject: "Add payment gateway integration"
- Prefix: PP (private)

**Before:** `PP#789: Add payment gateway integration`
**After:** `Add payment gateway integration — PP#789`

### Example 4: Long Title

**Work Package:**
- ID: 42
- Subject: "Improve asset ingestion performance for large video files"
- Prefix: OP

**Before:** `OP#42: Improve asset ingestion performance for large video files`
**After:** `Improve asset ingestion performance for large video files — OP#42`

## GitLab List View

### How Titles Appear in GitLab

**Issues List:**
```
📋 Implement user authentication — OP#123
   opened 2 hours ago by john.doe

📋 Fix login page crash on mobile — OP#456
   opened 1 day ago by jane.smith

📋 Add payment gateway integration — PP#789
   opened 3 days ago by bob.jones
```

**Benefits:**
- ✅ Task name is prominent
- ✅ Easy to scan and understand what each issue is about
- ✅ Reference is still visible but doesn't dominate

**Before (less clear):**
```
📋 OP#123: Implement user authentication
   opened 2 hours ago by john.doe
   ↑ Reference takes prominent position
```

## Search and Discovery

### GitLab Search Results

When users search for "authentication", they'll see:

**After (Better):**
```
Implement user authentication — OP#123
^^^^^^^^^^^^^^^^^^^^^^^^^
Subject matches search and appears first
```

**Before (Worse):**
```
OP#123: Implement user authentication
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
Subject hidden after prefix
```

## Complete Output Example

### Issue in GitLab

**Title:**
```
Improve asset ingestion performance — OP#123
```

**Description:**
```
This issue is related to OpenProject work package OP#123

**Work Package:** Improve asset ingestion performance

---

## Problem
Current asset ingestion is too slow for large files...

## Requirements
- Process files up to 5GB
- Maximum processing time: 30 seconds
...
```

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Create an Issue:**
1. Create a work package with subject: "Improve asset ingestion performance"
2. Go to GitLab tab
3. Click "Create Issue"
4. Open issue in GitLab
5. **Verify title**: `Improve asset ingestion performance — OP#123` ✅

**3. Create a Merge Request:**
1. Use the same or different work package
2. Click "Create MR"
3. Open MR in GitLab
4. **Verify title**: `{Subject} — OP#{id}` ✅

**4. Test Private Link:**
1. Check "Private link (PP#)" checkbox
2. Create Issue or MR
3. **Verify**: `{Subject} — PP#{id}` ✅

### Verification Checklist

- [ ] Issue title format: `{Subject} — OP#{id}`
- [ ] MR title format: `{Subject} — OP#{id}`
- [ ] Private issue title: `{Subject} — PP#{id}`
- [ ] Private MR title: `{Subject} — PP#{id}`
- [ ] Em dash (—) used as separator
- [ ] Subject appears first
- [ ] Reference appears at end

## Benefits Summary

### Better UX
- ✅ **Task-focused** - What it's about is immediately clear
- ✅ **Easier scanning** - Don't need to skip over reference
- ✅ **Better readability** - Natural reading order

### Better Organization
- ✅ **List views** - More meaningful at a glance
- ✅ **Search results** - Subject keywords appear first
- ✅ **Sorting** - Alphabetical sort is by subject

### Professional Appearance
- ✅ **Industry standard** - Matches common patterns
- ✅ **Typography** - Proper em dash usage
- ✅ **Consistent** - Same format for Issues and MRs

## Comparison

| Aspect | Before | After |
|--------|--------|-------|
| **Format** | `OP#123: Subject` | `Subject — OP#123` |
| **Focus** | Reference | Subject ✅ |
| **Readability** | Reference first | Natural order ✅ |
| **Scanning** | Skip reference | Direct to subject ✅ |
| **Separator** | Colon `:` | Em dash `—` ✅ |
| **Professional** | Standard | Enhanced ✅ |

## Character Details

### Em Dash in Ruby

The em dash is included as a literal character in the string:
```ruby
"#{work_package.subject} — #{prefix}##{work_package.id}"
                        ↑
                      em dash (—)
```

This is safe and supported:
- ✅ UTF-8 encoded
- ✅ Renders correctly in GitLab
- ✅ No escaping needed
- ✅ Works in all modern systems

### If Em Dash Causes Issues

If for any reason the em dash causes issues (encoding, display, etc.), alternatives:

**Option 1: Double hyphen**
```ruby
"#{work_package.subject} -- #{prefix}##{work_package.id}"
```

**Option 2: Pipe**
```ruby
"#{work_package.subject} | #{prefix}##{work_package.id}"
```

**Option 3: En dash**
```ruby
"#{work_package.subject} – #{prefix}##{work_package.id}"
```

But the em dash is recommended and should work fine! ✅

## Migration Note

**Existing Issues/MRs:**
- Old format titles remain unchanged
- Only **new** Issues/MRs use the new format
- No retroactive updates needed

**Consistency:**
- Eventually, all will use new format as new Issues/MRs are created
- Clear which ones are newer (better format)

## Summary

✅ **Changed title format to put subject first!**

**New Format:**
```
{Work Package Subject} — {Prefix}#{ID}
```

**Example:**
```
Improve asset ingestion performance — OP#123
```

**Benefits:**
- Subject is prominent
- Better scanning and readability
- Professional em dash separator
- Matches industry conventions

Just **restart your server** with `bin/dev` and new Issues/MRs will use the improved title format! 🎯

