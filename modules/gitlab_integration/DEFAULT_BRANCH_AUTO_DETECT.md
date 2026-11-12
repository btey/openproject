# Auto-Detect GitLab Default Branch for Merge Requests

## The Problem

The Create MR feature was hardcoded to use "main" as the target branch:

```ruby
target_branch: "main", # Hardcoded!
```

This caused issues because:
- ❌ Some projects use "master" as default
- ❌ Some projects use "develop" or custom branches
- ❌ Some projects don't have a "main" branch at all
- ❌ MR creation would fail if "main" doesn't exist

## The Solution

The service now **automatically fetches the GitLab project's default branch** using the GitLab API and uses it as the target branch.

## Implementation

### New Method: `fetch_gitlab_project_default_branch`

```ruby
def fetch_gitlab_project_default_branch
  uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}")

  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = uri.scheme == "https"

  request = Net::HTTP::Get.new(uri)
  request["PRIVATE-TOKEN"] = gitlab_config.access_token

  response = http.request(request)

  if response.is_a?(Net::HTTPSuccess)
    project_data = JSON.parse(response.body)
    project_data["default_branch"] || "main"
  else
    Rails.logger.warn "Failed to fetch GitLab project info, falling back to 'main' branch"
    "main"
  end
rescue StandardError => e
  Rails.logger.error "Error fetching GitLab default branch: #{e.message}"
  "main" # Fallback to 'main' if fetch fails
end
```

### Updated Payload

```ruby
def merge_request_payload
  {
    source_branch: branch_name,
    target_branch: fetch_gitlab_project_default_branch, # ← Dynamic!
    title: merge_request_title,
    description: merge_request_description,
    remove_source_branch: true
  }
end
```

## How It Works

### Flow

```
1. User clicks "Create MR"
   ↓
2. Service starts MR creation
   ↓
3. Fetch GitLab project info:
   GET /api/v4/projects/:id
   ↓
4. Extract default_branch from response
   ↓
5. Use default_branch as target_branch
   ↓
6. Create MR with correct target branch
   ↓
7. Success! MR created with proper target
```

### API Call

**Request:**
```
GET https://gitlab.com/api/v4/projects/mygroup%2Fmyproject
Headers:
  PRIVATE-TOKEN: <access_token>
```

**Response:**
```json
{
  "id": 12345,
  "name": "My Project",
  "default_branch": "develop",  // ← This is what we need!
  "path_with_namespace": "mygroup/myproject",
  // ...other fields
}
```

**Extracted Value:**
- `default_branch` → Used as `target_branch`
- Falls back to `"main"` if not found

## Fallback Strategy

The implementation has **multiple fallback levels**:

### Level 1: Success
```ruby
project_data["default_branch"]  # → "develop" (or whatever is configured)
```

### Level 2: Missing default_branch
```ruby
project_data["default_branch"] || "main"  # → "main" if key missing
```

### Level 3: API Failure
```ruby
rescue StandardError => e
  "main"  # → Fallback to "main" if API call fails
```

### Level 4: HTTP Error
```ruby
else
  Rails.logger.warn "Failed to fetch GitLab project info..."
  "main"
end
```

## Examples

### Example 1: Project Uses "master"

**GitLab Project:**
- Default branch: `master`

**Result:**
```ruby
target_branch: "master"  # ✅ Correct!
```

### Example 2: Project Uses "develop"

**GitLab Project:**
- Default branch: `develop`

**Result:**
```ruby
target_branch: "develop"  # ✅ Correct!
```

### Example 3: Project Uses "main"

**GitLab Project:**
- Default branch: `main`

**Result:**
```ruby
target_branch: "main"  # ✅ Correct!
```

### Example 4: API Call Fails

**Error:** Network timeout, invalid token, etc.

**Result:**
```ruby
target_branch: "main"  # ✅ Safe fallback
```

## Files Modified

- ✅ `lib/open_project/gitlab_integration/services/create_merge_request.rb`
  - Added `fetch_gitlab_project_default_branch` method
  - Updated `merge_request_payload` to use dynamic target branch
  - Added error handling with fallback to "main"

## Benefits

### ✅ Works With Any Default Branch
- master ✅
- main ✅
- develop ✅
- production ✅
- Any custom branch name ✅

### ✅ Prevents Errors
- No more "branch not found" errors
- No more failed MR creations due to missing "main"

### ✅ Respects GitLab Configuration
- Uses the actual default branch configured in GitLab
- Follows GitLab project conventions

### ✅ Safe Fallback
- If API call fails, falls back to "main"
- Logs warnings for debugging
- Never crashes the MR creation process

## Performance

### Additional API Call
- **One extra GET request** per MR creation
- Fetches project metadata (lightweight)
- Typically adds ~100-300ms

### Caching Consideration
Currently, the default branch is fetched for each MR creation. This could be optimized with caching if needed:

```ruby
# Future enhancement (not implemented):
def fetch_gitlab_project_default_branch
  Rails.cache.fetch(
    "gitlab_default_branch_#{gitlab_config.id}",
    expires_in: 1.hour
  ) do
    # ...fetch logic...
  end
end
```

## Error Handling

### Logged Warnings

**When API call fails:**
```
WARN: Failed to fetch GitLab project info, falling back to 'main' branch
```

**When exception occurs:**
```
ERROR: Error fetching GitLab default branch: <error message>
```

These logs help diagnose configuration issues (invalid token, wrong URL, etc.)

## Testing

### To Test:

**1. Restart Server:**
```bash
bin/dev
```

**2. Test with Different Default Branches:**

#### Test A: Project with "master" branch
1. Configure GitLab with a project that uses `master`
2. Create MR via OpenProject
3. Check GitLab → MR should target `master` ✅

#### Test B: Project with "develop" branch
1. Configure GitLab with a project that uses `develop`
2. Create MR via OpenProject
3. Check GitLab → MR should target `develop` ✅

#### Test C: Project with "main" branch
1. Configure GitLab with a project that uses `main`
2. Create MR via OpenProject
3. Check GitLab → MR should target `main` ✅

**3. Check Logs:**

After creating MR, check logs for:
- No warnings if API call succeeds ✅
- Warning message if API call fails ✅
- Error message if exception occurs ✅

### Expected Behavior

**Success Case:**
```
Rails log:
(no warnings - successful fetch)

GitLab MR:
Source: feature/op-123-task-title
Target: develop  ← Correct default branch!
```

**Fallback Case (API failure):**
```
Rails log:
WARN: Failed to fetch GitLab project info, falling back to 'main' branch

GitLab MR:
Source: feature/op-123-task-title
Target: main  ← Safe fallback
```

## API Reference

### GitLab API Endpoint

**Get Project:**
```
GET /api/v4/projects/:id
```

**Required Permission:**
- Read access to the project (access token must have at least `read_api` scope)

**Response Fields Used:**
- `default_branch` (string) - The name of the default branch

**Documentation:**
https://docs.gitlab.com/ee/api/projects.html#get-single-project

## Common Default Branch Names

The implementation now works with all of these:

| Branch Name | Usage |
|-------------|-------|
| `main` | GitHub/GitLab modern default |
| `master` | Traditional default |
| `develop` | Gitflow development branch |
| `development` | Common variant |
| `staging` | Some teams use this |
| `production` | Direct production deploys |
| Custom names | Any branch name configured in GitLab |

## Future Enhancements

### Possible Improvements:

1. **Cache default branch** for 1 hour to reduce API calls
2. **Allow manual override** in GitLab Setup form
3. **Validate branch exists** before creating MR
4. **Support source branch** auto-detection (check if branch already exists)

### Manual Override Example (not implemented):

```ruby
# In GitLab Setup form, add optional field:
# "Target Branch Override" (defaults to empty = auto-detect)

def target_branch
  gitlab_config.target_branch_override.presence || 
    fetch_gitlab_project_default_branch
end
```

## Summary

🎯 **Merge Requests now automatically use the correct default branch from GitLab!**

**Before:**
- Target branch: Always "main" (hardcoded)
- ❌ Failed if project didn't have "main"

**After:**
- Target branch: Auto-detected from GitLab project
- ✅ Works with master, develop, or any default branch
- ✅ Safe fallback to "main" if detection fails

**No configuration needed** - it just works! The service automatically fetches the project's default branch and uses it.

Just **restart your server** with `bin/dev` and test creating MRs in projects with different default branches! 🚀

