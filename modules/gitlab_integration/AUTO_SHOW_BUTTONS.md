# Auto-Show Create Buttons After Configuration

## The Problem

When saving GitLab configuration for the first time (in a project without existing GitLab setup), the Create Issue and Create MR buttons (and their checkboxes) remained hidden. Users had to manually refresh the page to see the buttons appear.

## The Solution

Implemented a **reactive notification system** using RxJS that automatically notifies all header components when the GitLab configuration is saved, triggering them to re-check the configuration and show the buttons immediately.

## Architecture

### Event Bus Pattern

Created a shared service that acts as an event bus:

```typescript
@Injectable({ providedIn: 'root' })
export class GitlabConfigurationService {
  private configurationUpdated$ = new Subject<void>();
  public onConfigurationUpdated$ = this.configurationUpdated$.asObservable();

  public notifyConfigurationUpdated():void {
    this.configurationUpdated$.next();
  }
}
```

### Flow

1. **User saves configuration** → GitLab Setup component
2. **Configuration saved successfully** → Notify via service
3. **Event broadcast** → All subscribed components notified
4. **Components re-check** → Fetch latest configuration
5. **Buttons appear** → If configuration is complete

```
┌─────────────────────┐
│  GitLab Setup       │
│  (saves config)     │
└──────────┬──────────┘
           │
           │ notifyConfigurationUpdated()
           ↓
┌─────────────────────────────┐
│ GitlabConfigurationService  │
│ (event bus)                 │
└──────────┬──────────────────┘
           │
           │ onConfigurationUpdated$
           ├────────────┬──────────────┐
           ↓            ↓              ↓
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Issue   │  │    MR    │  │  Future  │
    │  Header  │  │  Header  │  │Components│
    └──────────┘  └──────────┘  └──────────┘
           │            │
           │ checkGitlabConfiguration()
           ↓            ↓
    Buttons appear if configured!
```

## Implementation Details

### 1. GitlabConfigurationService (New)

**File**: `frontend/module/gitlab-configuration.service.ts`

- Uses RxJS `Subject` for event broadcasting
- Provides `onConfigurationUpdated$` observable for subscriptions
- Provides `notifyConfigurationUpdated()` method to trigger events
- Registered as singleton (`providedIn: 'root'`)

### 2. GitLab Setup Component

**File**: `frontend/module/gitlab-setup/gitlab-setup.component.ts`

**Changes**:
- Injects `GitlabConfigurationService`
- Calls `notifyConfigurationUpdated()` after successful save

```typescript
this.http.patch<GitlabConfiguration>(apiUrl, data).subscribe({
  next: (config) => {
    // ...update form...
    this.showMessage('Configuration saved successfully!', 'success');
    
    // Notify other components
    this.gitlabConfigService.notifyConfigurationUpdated();
  },
  // ...
});
```

### 3. Issue Header Component

**File**: `frontend/module/tab-header-issue/tab-header-issue.component.ts`

**Changes**:
- Implements `OnDestroy` interface
- Adds `configSubscription` property for cleanup
- Subscribes to `onConfigurationUpdated$` in `ngOnInit()`
- Unsubscribes in `ngOnDestroy()` to prevent memory leaks
- Re-checks configuration when notified

```typescript
ngOnInit():void {
  this.checkGitlabConfiguration();
  
  // Subscribe to configuration updates
  this.configSubscription = this.gitlabConfigService.onConfigurationUpdated$.subscribe(() => {
    console.log('[Issue Header] Configuration updated, re-checking...');
    this.checkGitlabConfiguration();
  });
}

ngOnDestroy():void {
  this.configSubscription?.unsubscribe();
}
```

### 4. MR Header Component

**File**: `frontend/module/tab-header-mr/tab-header-mr.component.ts`

**Changes**: Same as Issue Header Component
- Implements `OnDestroy`
- Subscribes to configuration updates
- Re-checks configuration when notified
- Properly cleans up subscription

## Files Created

- ✅ `frontend/module/gitlab-configuration.service.ts` - Event bus service

## Files Modified

**Backend**: None (purely frontend change)

**Frontend**:
- ✅ `frontend/module/gitlab-setup/gitlab-setup.component.ts` - Notify on save
- ✅ `frontend/module/tab-header-issue/tab-header-issue.component.ts` - Subscribe to updates
- ✅ `frontend/module/tab-header-mr/tab-header-mr.component.ts` - Subscribe to updates
- ✅ `frontend/module/main.ts` - Register new service

## User Experience

### Before This Fix

```
1. User goes to project without GitLab configured
2. Opens GitLab tab → No Create buttons visible ✅
3. Clicks "GitLab Setup", fills form, saves
4. Success message appears ✅
5. Create buttons still hidden ❌
6. User must refresh page manually ❌
7. After refresh: Buttons appear ✅
```

### After This Fix

```
1. User goes to project without GitLab configured
2. Opens GitLab tab → No Create buttons visible ✅
3. Clicks "GitLab Setup", fills form, saves
4. Success message appears ✅
5. Create buttons appear automatically! ✅ (NEW!)
6. No page refresh needed! ✅ (NEW!)
```

## Benefits

### ✅ Better UX
- No manual page refresh required
- Immediate feedback when configuration is saved
- Seamless workflow from setup to creating issues/MRs

### ✅ Reactive Architecture
- Event-driven design
- Loose coupling between components
- Easy to extend (other components can subscribe)

### ✅ Proper Resource Management
- Subscriptions properly cleaned up in `ngOnDestroy()`
- No memory leaks
- Follows Angular best practices

### ✅ Console Logging
- Debug logs help track the flow
- Can see when configuration is updated
- Can see when components re-check

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Test Auto-Show Behavior:**

**Step 1**: Go to project **without** GitLab configured
- Open GitLab tab
- **Expected**: No Create buttons visible ✅

**Step 2**: Configure GitLab
- Click "GitLab Setup" button
- Fill in:
  - GitLab URL: `https://gitlab.com`
  - Project Identifier: `mygroup/myproject`
  - Access Token: `test-token`
- Click "Save"

**Step 3**: Verify Auto-Show
- **Expected**: Success message appears ✅
- **Expected**: Create buttons appear **immediately** (no refresh!) ✅
- **Expected**: Checkboxes appear ✅
- **Expected**: Console shows:
  ```
  [GitLab Setup] Save completed in XXXms
  [Issue Header] Configuration updated, re-checking...
  [MR Header] Configuration updated, re-checking...
  ```

**Step 4**: Test Buttons Work
- Check "Private link" checkbox
- Click "Create Issue"
- **Expected**: Issue created with PP# prefix ✅

### Browser Console Output

After saving configuration, you should see:
```
[GitLab Setup] Save completed in 234ms at: 2025-11-27T...
Saved configuration: {gitlabUrl: "...", projectIdentifier: "...", accessTokenPresent: true}
[Issue Header] Configuration updated, re-checking...
Loaded configuration: {gitlabUrl: "...", ...}
[MR Header] Configuration updated, re-checking...
Loaded configuration: {gitlabUrl: "...", ...}
```

This confirms:
1. Configuration was saved
2. Event was broadcast
3. Both components received the event
4. Both components re-checked configuration

## Technical Details

### RxJS Subject vs BehaviorSubject

We use a simple `Subject` (not `BehaviorSubject`) because:
- ✅ We don't need to replay the last value to new subscribers
- ✅ We only care about future configuration updates
- ✅ Components check configuration on `ngOnInit()` anyway
- ✅ Simpler and more efficient

### Memory Leak Prevention

All components properly unsubscribe in `ngOnDestroy()`:
```typescript
ngOnDestroy():void {
  this.configSubscription?.unsubscribe();
}
```

This prevents:
- ❌ Memory leaks from hanging subscriptions
- ❌ Components reacting after being destroyed
- ❌ Multiple subscriptions piling up

### Singleton Service

The service is registered as `providedIn: 'root'`, making it:
- ✅ A singleton (one instance for entire app)
- ✅ Available to all components
- ✅ Automatically tree-shaken if not used

## Future Enhancements

This pattern can be extended to:
1. **Notify when configuration is deleted** (hide buttons)
2. **Notify when configuration is updated** (validate buttons still work)
3. **Other components** can subscribe (e.g., issue/MR lists to refresh)
4. **Emit configuration data** instead of void (if components need the actual config)

Example:
```typescript
private configurationUpdated$ = new Subject<GitlabConfiguration>();
```

## Summary

🎉 **Create buttons now appear automatically after saving GitLab configuration!**

No more manual page refreshes - the buttons show up immediately thanks to a reactive event-driven architecture using RxJS.

**Technical highlights:**
- Event bus pattern with RxJS `Subject`
- Proper subscription cleanup to prevent memory leaks
- Console logging for debugging
- Loose coupling between components

Just **restart your server** with `bin/dev` and test it - save GitLab configuration and watch the buttons appear instantly! 🚀

