# GitLab Merge Request Creation Feature

## Overview

This feature allows users to create GitLab Merge Requests directly from OpenProject work packages through a "Create MR" button in the GitLab integration tab.

## Setup

### 1. Database Migration

Run the migration to create the `gitlab_configurations` table:

```bash
bundle exec rake db:migrate
```

### 2. Install Dependencies

The feature requires the `attr_encrypted` gem for secure token storage. Install it:

```bash
bundle install
```

### 3. Configure GitLab Integration

For each project that wants to use the "Create MR" feature, you need to configure:

1. **GitLab URL**: The base URL of your GitLab instance (e.g., `https://gitlab.com` or `https://gitlab.yourcompany.com`)
2. **Project Identifier**: The GitLab project ID or path (e.g., `group/project-name` or numeric ID)
3. **Access Token**: A GitLab Personal Access Token or Project Access Token with `api` scope

#### Creating a GitLab Access Token

1. In GitLab, go to **Settings** → **Access Tokens**
2. Create a new token with:
   - Name: `OpenProject Integration`
   - Scopes: `api` (required to create merge requests)
   - Expiration: Optional (recommended to set for security)
3. Copy the generated token

#### Storing Configuration

Currently, you can configure GitLab settings via Rails console:

```ruby
# In Rails console (bundle exec rails console)
project = Project.find_by(identifier: 'your-project-identifier')

GitlabConfiguration.create!(
  project: project,
  gitlab_url: 'https://gitlab.com',
  project_identifier: 'group/project-name',
  access_token: 'your-gitlab-access-token'
)
```

### 4. Frontend Build

After updating frontend code, rebuild the assets:

```bash
cd frontend
npm install
cd ..
bundle exec rails openproject:plugins:register_frontend assets:export_locales
```

Or use the development server:

```bash
bin/dev
```

## Usage

Once configured:

1. Open a work package in a project with GitLab integration configured
2. Navigate to the **GitLab** tab
3. In the **Merge Requests** section, click the **Create MR** button next to "Git snippets"
4. The system will:
   - Create a new merge request in GitLab
   - Set the title as `OP#<id>: <work package subject>`
   - Include work package details in the description
   - Open the created MR in a new browser tab

## How It Works

### Backend

- **Model**: `GitlabConfiguration` - Stores GitLab credentials per project
- **Service**: `OpenProject::GitlabIntegration::Services::CreateMergeRequest` - Handles MR creation via GitLab API
- **API**: `API::V3::GitlabMergeRequests::CreateGitlabMergeRequestAPI` - Exposes endpoint for frontend

### Frontend

- **Service**: `GitlabMergeRequestService` - Angular service for API calls
- **Component**: `TabHeaderMrsComponent` - Updated to include Create MR button
- **Template**: `tab-header-mr.template.html` - UI with button

### API Endpoint

```
POST /api/v3/work_packages/:id/create_gitlab_merge_request
```

### Security

- Access tokens are stored in the database
- **Important**: For production use, enable database encryption at rest
- Requires `show_gitlab_content` permission
- Tokens are never exposed in API responses
- Restrict database access to authorized personnel only

## Merge Request Details

When creating an MR, the system:

- **Source Branch**: `feature/op-<id>-<slugified-subject>`
- **Target Branch**: `main` (configurable in code)
- **Title**: `OP#<id>: <work package subject>`
- **Description**: Includes work package reference and truncated description
- **Auto-remove source branch**: Enabled

**Note**: The source branch must exist in GitLab before creating the MR. This feature assumes the branch will be created manually or through the Git snippets workflow.

## Future Enhancements

Potential improvements:

1. **Admin UI**: Web interface for managing GitLab configurations instead of console
2. **Branch Creation**: Automatically create the source branch via API
3. **Configurable Target Branch**: Allow per-project target branch configuration
4. **Multiple GitLab Instances**: Support multiple GitLab projects per OpenProject project
5. **Validation**: Check if branch exists before creating MR
6. **Template Support**: Customizable MR description templates

## Troubleshooting

### "GitLab not configured for this project"

Ensure `GitlabConfiguration` exists for the project with all required fields.

### "Failed to create merge request"

Common causes:
- Invalid access token
- Missing `api` scope on token
- Source branch doesn't exist in GitLab
- Invalid project identifier
- Network connectivity issues

Check Rails logs for detailed error messages:

```bash
tail -f log/development.log
```

## Contributing

When modifying this feature:

1. Follow OpenProject coding guidelines
2. Run linters: `bundle exec rubocop` and `cd frontend && npx eslint src/`
3. Write tests for new functionality
4. Update this documentation

## License

GPLv3 - See LICENSE file

