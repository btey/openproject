# Fix Buttons Disappearing When Switching Work Packages

## The Problem

When viewing the GitLab tab and switching to a different work package **without changing tabs**, the Create Issue and Create MR buttons would:
- ❌ Disappear immediately
- ❌ Take several seconds to reappear (or not appear at all)
- ✅ Only reappear instantly when clicking the GitLab tab again

This created a poor user experience where buttons seemed to randomly vanish.

## Root Cause

### Angular Component Lifecycle Issue

Angular's `ngOnInit()` lifecycle hook only runs **once** when a component is first created. When switching between work packages while staying on the same tab:

1. **Angular reuses the same component instance** (performance optimization)
2. **Only the `@Input()` property is updated** (the `workPackage` property)
3. **`ngOnInit()` does NOT run again**
4. **Configuration check never happens** for the new work package
5. **Buttons stay hidden** because `isGitlabConfigured` is still `false` from the old work package

### Why Clicking the Tab Fixed It

When you click the GitLab tab again:
- Angular destroys and recreates the component
- `ngOnInit()` runs again
- Configuration is checked for the current work package
- Buttons appear correctly ✅

## The Solution

Implemented the **`OnChanges` lifecycle hook** to detect when the work package changes and re-check the configuration immediately.

### How It Works

```typescript
ngOnChanges(changes: SimpleChanges):void {
  // Re-check configuration when work package changes
  if (changes['workPackage'] && !changes['workPackage'].firstChange) {
    console.log('[Issue Header] Work package changed, re-checking configuration...');
    this.checkGitlabConfiguration();
  }
}
```

**Flow:**
1. User switches to different work package
2. Angular updates `workPackage` input property
3. `ngOnChanges()` detects the change
4. `checkGitlabConfiguration()` runs for new work package
5. Buttons appear/disappear based on new work package's project configuration
6. **Instant update!** ✅

## Implementation

### Issue Header Component

**File**: `frontend/module/tab-header-issue/tab-header-issue.component.ts`

```typescript
// Add OnChanges to imports
import { Component, Input, OnInit, OnDestroy, OnChanges, SimpleChanges } from '@angular/core';

// Add OnChanges to implements
export class TabHeaderIssueComponent implements OnInit, OnDestroy, OnChanges {
  
  // Existing ngOnInit...
  
  // NEW: Detect work package changes
  ngOnChanges(changes: SimpleChanges):void {
    if (changes['workPackage'] && !changes['workPackage'].firstChange) {
      console.log('[Issue Header] Work package changed, re-checking configuration...');
      this.checkGitlabConfiguration();
    }
  }
  
  // Existing ngOnDestroy...
}
```

### MR Header Component

**File**: `frontend/module/tab-header-mr/tab-header-mr.component.ts`

Same implementation - added `OnChanges` and `ngOnChanges()` method.

## Files Modified

- ✅ `frontend/module/tab-header-issue/tab-header-issue.component.ts` - Added OnChanges
- ✅ `frontend/module/tab-header-mr/tab-header-mr.component.ts` - Added OnChanges

## Lifecycle Hooks Explained

### Before (Broken)

**Component Lifecycle:**
```
1. Component created → ngOnInit() runs → Check config ✅
2. Work package switches → (nothing happens) ❌
3. Work package switches again → (nothing happens) ❌
4. User clicks tab → Component destroyed & recreated → ngOnInit() runs → Check config ✅
```

### After (Fixed)

**Component Lifecycle:**
```
1. Component created → ngOnInit() runs → Check config ✅
2. Work package switches → ngOnChanges() runs → Check config ✅
3. Work package switches again → ngOnChanges() runs → Check config ✅
4. Buttons always correct for current work package! ✅
```

## Why `!changes['workPackage'].firstChange`?

The check `!changes['workPackage'].firstChange` prevents running the check twice on initial load:

```typescript
if (changes['workPackage'] && !changes['workPackage'].firstChange) {
  // Only run for subsequent changes, not initial load
}
```

**Reasoning:**
- `ngOnInit()` already checks configuration on first load
- `ngOnChanges()` runs **before** `ngOnInit()` on first load
- Without this check, we'd check configuration twice initially (wasteful)
- We only want to check when work package **changes** after initial load

## User Experience

### Before (Broken)

```
Step 1: View WP #123 → GitLab tab
        Buttons visible ✅

Step 2: Switch to WP #456 (same tab)
        Buttons disappear ❌
        Wait... still missing ❌
        
Step 3: Click GitLab tab again
        Buttons appear ✅ (but requires extra click)
```

### After (Fixed)

```
Step 1: View WP #123 → GitLab tab
        Buttons visible ✅

Step 2: Switch to WP #456 (same tab)
        Buttons update instantly ✅
        (appear or disappear based on #456's project config)
        
Step 3: Switch to WP #789 (same tab)
        Buttons update instantly ✅
        No extra clicks needed!
```

## Console Logs

With the fix, you'll see these logs when switching work packages:

```
[Issue Header] Work package changed, re-checking configuration...
Loaded configuration: {gitlabUrl: "...", projectIdentifier: "...", ...}
[MR Header] Work package changed, re-checking configuration...
Loaded configuration: {gitlabUrl: "...", projectIdentifier: "...", ...}
```

This confirms the configuration is being checked for each work package.

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Test Work Package Switching:**

1. **Open Work Package #1** in a project **with** GitLab configured
   - Go to GitLab tab
   - **Verify**: Buttons visible ✅

2. **Switch to Work Package #2** (same project) **without clicking tabs**
   - **Verify**: Buttons remain visible ✅
   - **Verify**: No delay, instant update ✅

3. **Switch to Work Package #3** in a project **without** GitLab configured
   - **Verify**: Buttons disappear immediately ✅
   - **Verify**: No delay ✅

4. **Switch back to Work Package #1**
   - **Verify**: Buttons reappear immediately ✅

5. **Check browser console**
   - **Verify**: See "Work package changed, re-checking configuration..." logs ✅

### Expected Behavior

✅ **Buttons appear instantly** when switching to WP with GitLab configured
✅ **Buttons disappear instantly** when switching to WP without GitLab configured
✅ **No delays** or waiting periods
✅ **No need to click tab** to refresh
✅ **Console logs** show configuration checks

## Edge Cases

### Case 1: Switching Between WPs in Same Project

Both work packages are in the same project (same GitLab config):
- Buttons remain visible ✅
- Configuration is re-checked but result is the same
- Seamless experience

### Case 2: Switching Between Different Projects

Work packages are in different projects:
- **Project A has GitLab** → Buttons visible
- **Switch to WP in Project B (no GitLab)** → Buttons disappear immediately
- **Switch back to WP in Project A** → Buttons reappear immediately

### Case 3: Fast Switching

User rapidly switches between multiple work packages:
- Each switch triggers `ngOnChanges()`
- Configuration checked for each WP
- May see multiple API calls (one per WP)
- Buttons always correct for current WP ✅

### Case 4: Initial Load

When first opening a work package:
- `ngOnChanges()` runs (but skipped via `firstChange` check)
- `ngOnInit()` runs and checks configuration
- Buttons appear correctly ✅
- No duplicate API calls

## Performance

### API Calls

**Before:**
- 1 API call per component on initial load
- 1 API call when clicking tab (recreates component)

**After:**
- 1 API call per component on initial load
- 1 API call per component when work package changes
- **More API calls** but better UX ✅

### Optimization Opportunities (Not Implemented)

Could cache configuration per project:

```typescript
// Future enhancement:
private configCache = new Map<string, boolean>();

checkGitlabConfiguration():void {
  const projectId = this.workPackage.project.id;
  
  if (this.configCache.has(projectId)) {
    this.isGitlabConfigured = this.configCache.get(projectId);
    return;
  }
  
  // Fetch from API and cache...
}
```

But current solution is simple and works well!

## Benefits

✅ **Instant Updates** - Buttons appear/disappear immediately when switching WPs
✅ **No Extra Clicks** - Don't need to click tab to refresh
✅ **Better UX** - Seamless work package navigation
✅ **Predictable** - Buttons always correct for current WP
✅ **Debug Logs** - Console shows what's happening

## Angular Lifecycle Hooks Summary

For reference, the component now uses:

| Hook | When It Runs | Purpose |
|------|--------------|---------|
| `ngOnInit()` | Once on component creation | Initial configuration check |
| `ngOnChanges()` | When `@Input()` properties change | Re-check when WP changes |
| `ngOnDestroy()` | When component is destroyed | Clean up subscriptions |

## Summary

✅ **Fixed buttons disappearing when switching work packages!**

**Problem:**
- Buttons disappeared when switching work packages
- Only reappeared when clicking tab again

**Solution:**
- Added `OnChanges` lifecycle hook
- Re-check configuration when work package changes
- Instant button visibility updates

**Result:**
- Buttons always correct for current work package
- No delays or extra clicks needed
- Seamless navigation experience

Just **restart your server** with `bin/dev` and test switching between work packages - the buttons will now update instantly! 🎯

