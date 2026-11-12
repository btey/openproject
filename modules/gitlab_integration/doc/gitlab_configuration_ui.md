# GitLab Configuration UI

This feature adds a user interface to manage GitLab configurations per project through the GitLab tab in work packages.

## Overview

The GitLab Setup section appears at the top of the GitLab tab (above the Issues section) and allows project administrators to configure the GitLab integration settings for their project.

## Features

### UI Components

1. **GitLab Setup Button**: A toggle button visible only to users with the `manage_gitlab_configuration` permission
2. **Configuration Form**: Contains three fields:
   - **GitLab URL**: The base URL of your GitLab instance (e.g., `https://gitlab.com`)
   - **Project Identifier**: The full path to your GitLab project (e.g., `username/project-name`)
   - **Access Token**: A GitLab personal access token for API authentication (displayed as password field)

### Automatic Record Creation

When the GitLab tab loads, the system automatically creates a `GitlabConfiguration` record for the project if one doesn't exist. This ensures that:
- The `project_id` is set to the current OpenProject project's ID
- Timestamps (`created_at`, `updated_at`) are automatically managed
- The record is ready to be populated with configuration data

### Permissions

- **Viewing the GitLab tab**: Requires `show_gitlab_content` permission
- **Managing configuration**: Requires `manage_gitlab_configuration` permission
  - This permission depends on `show_gitlab_content`
  - Only users with this permission will see the GitLab Setup button

## API Endpoints

### GET `/api/v3/projects/:project_id/gitlab_configuration`

Retrieves the GitLab configuration for a project. Auto-creates an empty record if none exists.

**Required Permission**: `show_gitlab_content`

**Response**:
```json
{
  "_type": "GitlabConfiguration",
  "id": 1,
  "project_id": 42,
  "gitlab_url": "https://gitlab.com",
  "project_identifier": "mygroup/myproject",
  "access_token_present": true
}
```

Note: The actual `access_token` value is never returned for security reasons. Only `access_token_present` (boolean) is included.

### PATCH `/api/v3/projects/:project_id/gitlab_configuration`

Updates the GitLab configuration for a project. Auto-creates the record if it doesn't exist.

**Required Permission**: `manage_gitlab_configuration`

**Request Body**:
```json
{
  "gitlab_url": "https://gitlab.example.com",
  "project_identifier": "mygroup/myproject",
  "access_token": "glpat-xxxxxxxxxxxxx"
}
```

All fields are optional in the request. Only provided fields will be updated.

**Response**: Same as GET endpoint

## Database Schema

The `gitlab_configurations` table includes:

- `id`: Primary key
- `project_id`: Foreign key to projects table (unique index)
- `gitlab_url`: String (nullable)
- `project_identifier`: String (nullable)
- `access_token`: Text (nullable)
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Frontend Implementation

### Angular Component

- **Component**: `GitlabSetupComponent`
- **Location**: `frontend/module/gitlab-setup/`
- **Files**:
  - `gitlab-setup.component.ts` - Component logic
  - `gitlab-setup.template.html` - HTML template
  - `gitlab-setup.component.sass` - Styles

### Integration

The component is integrated into the main GitLab tab template at the top, before the Issues section.

## Validation

The model includes conditional validation:
- Fields are only validated on update if any configuration field has been set
- This allows empty records to be created initially
- URL format validation on `gitlab_url` when present

## Security Considerations

1. **Access Token Storage**: Currently stored as plain text in the database
   - For production use, ensure database encryption at rest is enabled
   - Consider implementing application-level encryption

2. **API Response**: The actual access token is never exposed through the API
   - Only a boolean `access_token_present` is returned
   - Users must re-enter the token to change it

3. **Permissions**: The `manage_gitlab_configuration` permission controls who can modify settings

## Testing

Run the RSpec tests:

```bash
bundle exec rspec modules/gitlab_integration/spec/requests/api/v3/gitlab_configuration_spec.rb
bundle exec rspec modules/gitlab_integration/spec/models/gitlab_configuration_spec.rb
```

## Future Enhancements

1. Implement application-level encryption for access tokens
2. Add validation to test the GitLab connection before saving
3. Add audit logging for configuration changes
4. Support for multiple GitLab instances per project

