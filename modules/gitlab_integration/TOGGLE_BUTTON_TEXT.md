# Toggle GitLab Setup Button Text

## What Was Changed

The GitLab Setup button now shows dynamic text based on whether the form is visible or hidden:
- **Form hidden**: "Show GitLab Setup"
- **Form visible**: "Hide GitLab Setup"

## Implementation

### Template Update

**File**: `frontend/module/gitlab-setup/gitlab-setup.template.html`

```html
<!-- Before: Static text -->
<span class="button--text">GitLab Setup</span>

<!-- After: Dynamic text -->
<span class="button--text">{{ showForm ? text.hideSetup : text.showSetup }}</span>
```

### Component Update

**File**: `frontend/module/gitlab-setup/gitlab-setup.component.ts`

Added text properties:
```typescript
public text = {
  showSetup: this.I18n.t('js.gitlab_integration.gitlab_setup.show'),
  hideSetup: this.I18n.t('js.gitlab_integration.gitlab_setup.hide'),
};
```

### Translations Added

**File**: `config/locales/js-en.yml`

```yaml
gitlab_setup:
  show: "Show GitLab Setup"
  hide: "Hide GitLab Setup"
```

## Files Modified

- ✅ `frontend/module/gitlab-setup/gitlab-setup.template.html` - Dynamic button text
- ✅ `frontend/module/gitlab-setup/gitlab-setup.component.ts` - Added text properties
- ✅ `config/locales/js-en.yml` - Added translations

## Expected Behavior

### When Form is Hidden
```
[Show GitLab Setup]  ← Button text
```

### When Form is Visible
```
[Hide GitLab Setup]  ← Button text changes
  GitLab URL: [____________]
  Project Identifier: [____________]
  Access Token: [____________]
  [Save]
```

## User Experience

**Before:**
- Button always showed "GitLab Setup"
- No indication whether clicking would show or hide the form

**After:**
- Button shows "Show GitLab Setup" when form is hidden
- Button shows "Hide GitLab Setup" when form is visible
- Clear indication of what the button will do

## Benefits

✅ **Better UX** - Clear button labels indicate action
✅ **Standard pattern** - Common show/hide toggle behavior
✅ **Accessible** - Users know what clicking will do
✅ **Consistent** - Follows UI conventions

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Test Button Toggle:**
1. Go to a work package in a project with GitLab enabled
2. Click the GitLab tab
3. **Expected**: Button shows "Show GitLab Setup" ✅
4. Click the button
5. **Expected**: Form appears, button now shows "Hide GitLab Setup" ✅
6. Click the button again
7. **Expected**: Form hides, button shows "Show GitLab Setup" ✅

### Verification Steps

- [ ] Button shows "Show GitLab Setup" initially
- [ ] Clicking button shows the form
- [ ] Button text changes to "Hide GitLab Setup"
- [ ] Clicking button again hides the form
- [ ] Button text changes back to "Show GitLab Setup"
- [ ] Aria-expanded attribute updates correctly

## Accessibility

The button maintains proper accessibility attributes:
```html
[attr.aria-expanded]="showForm"
```

This tells screen readers whether the content is expanded or collapsed, in addition to the text change.

## Similar Patterns

This follows common UI patterns seen in:
- Accordion components ("Show more" / "Show less")
- Collapsible sections ("Expand" / "Collapse")
- Detail toggles ("Show details" / "Hide details")

## Summary

✅ **Button text now changes dynamically!**

- **Hidden**: "Show GitLab Setup"
- **Visible**: "Hide GitLab Setup"

This makes it clear to users what will happen when they click the button.

Just **restart your server** with `bin/dev` and the button will show the appropriate text based on form visibility! 🎯

