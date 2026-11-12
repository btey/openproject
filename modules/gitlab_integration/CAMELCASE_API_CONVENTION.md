# OpenProject API CamelCase Convention

## The Issue

OpenProject's API v3 uses **CamelCasingStrategy** for all JSON responses. This means:
- Database columns use `snake_case`
- API requests accept `snake_case` parameters
- **API responses return `camelCase` properties**

## Example

### Database/Model
```ruby
class GitlabConfiguration < ApplicationRecord
  # Columns in database:
  # - gitlab_url
  # - project_identifier
  # - access_token
end
```

### API Representer
```ruby
class GitlabConfigurationRepresenter < ::API::Decorators::Single
  property :gitlab_url        # Defined in snake_case
  property :project_identifier
  property :access_token_present
end
```

### API Response (JSON)
```json
{
  "id": 1,
  "projectId": 1,
  "gitlabUrl": "https://gitlab.com",
  "projectIdentifier": "mygroup/myproject",
  "accessTokenPresent": true
}
```

### TypeScript Interface
```typescript
interface GitlabConfiguration {
  id: number;
  projectId: number;              // camelCase!
  gitlabUrl: string | null;       // camelCase!
  projectIdentifier: string | null; // camelCase!
  accessTokenPresent: boolean;    // camelCase!
}
```

## Why This Happens

The `API::Decorators::Single` base class (used by all OpenProject API representers) has this configuration:

```ruby
class Single < ::Roar::Decorator
  self.as_strategy = ::API::Utilities::CamelCasingStrategy.new
  # ...
end
```

This automatically converts all property names to camelCase in JSON output.

## Request vs Response

| Direction | Format | Example |
|-----------|--------|---------|
| **Request body** (POST/PATCH) | `snake_case` | `{ gitlab_url: "..." }` |
| **Response body** (GET/POST/PATCH) | `camelCase` | `{ gitlabUrl: "..." }` |
| **URL parameters** | `snake_case` | `?project_id=1` |

## Common Mistakes

### ❌ Wrong
```typescript
interface Config {
  gitlab_url: string;  // Won't match API response!
}

this.url = config.gitlab_url;  // Will be undefined!
```

### ✅ Correct
```typescript
interface Config {
  gitlabUrl: string;  // Matches API response
}

this.url = config.gitlabUrl;  // Works!
```

## How to Debug

1. **Check the API response** in browser Network tab
2. **Add console.log** to see the actual structure:
   ```typescript
   console.log('API response:', response);
   ```
3. **Look for camelCase** properties in the output

## Rules of Thumb

1. **Backend Ruby code**: Always use `snake_case`
2. **API representers**: Define properties in `snake_case` (they'll be converted automatically)
3. **TypeScript/JavaScript**: Always use `camelCase` when consuming API responses
4. **Sending data TO API**: Use `snake_case` in request bodies
5. **Receiving data FROM API**: Expect `camelCase` in responses

## Examples from OpenProject Codebase

Check these files for examples:
- `/lib/api/v3/users/user_representer.rb` - Backend representer
- `/frontend/src/app/features/hal/resources/user-resource.ts` - Frontend interface
- `/lib/api/v3/work_packages/work_package_representer.rb` - Complex example

## Testing API Responses

```bash
# Make an API request and see the response format
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:3000/api/v3/projects/1/gitlab_configuration | jq
```

Look for camelCase in the output:
```json
{
  "gitlabUrl": "...",          # camelCase!
  "projectIdentifier": "..."   # camelCase!
}
```

## Summary

**Remember**: When working with OpenProject API v3:
- **Send**: `snake_case` ✉️
- **Receive**: `camelCase` 📬

