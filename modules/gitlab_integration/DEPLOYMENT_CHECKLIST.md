# GitLab Configuration UI - Deployment Checklist

## Pre-Deployment Steps

### 1. Database Migration
The migration has been updated to allow nullable fields. You need to:

```bash
# If you've already run the migration with non-nullable fields, you need to modify the table
bundle exec rails db:migrate:status

# Check if migration 20250126000001 has run
# If yes, you may need to create a new migration to modify columns:

bundle exec rails generate migration AllowNullableGitlabConfigurationFields

# Then manually edit the migration file to:
# change_column_null :gitlab_configurations, :gitlab_url, true
# change_column_null :gitlab_configurations, :project_identifier, true

# Then run:
bundle exec rake db:migrate
```

**OR** if the migration hasn't run yet:
```bash
bundle exec rake db:migrate
```

### 2. Frontend Build
```bash
# Install dependencies if needed
cd frontend && npm install

# Build frontend assets
npm run build

# OR use the dev server
cd ..
bin/dev
```

### 3. Update Permissions

Add the new `manage_gitlab_configuration` permission to appropriate roles:

1. Go to Administration → Roles and permissions
2. Edit the roles that should manage GitLab configuration (e.g., Project Admin)
3. Under "GitLab" module permissions, enable:
   - `show_gitlab_content` (to view)
   - `manage_gitlab_configuration` (to edit)

## Testing Steps

### 1. Run Backend Tests
```bash
# Test the model
bundle exec rspec modules/gitlab_integration/spec/models/gitlab_configuration_spec.rb

# Test the API endpoints
bundle exec rspec modules/gitlab_integration/spec/requests/api/v3/gitlab_configuration_spec.rb

# Test the UI (requires frontend running)
bundle exec rspec modules/gitlab_integration/spec/features/gitlab_configuration_ui_spec.rb
```

### 2. Run Frontend Tests
```bash
cd frontend
npm test
```

### 3. Manual Testing

1. **Create a test project**
   - Enable the GitLab module
   - Create a work package

2. **Test as admin user**
   - Open the work package
   - Go to GitLab tab
   - Verify "GitLab Setup" button appears
   - Click button to expand form
   - Fill in configuration:
     - GitLab URL: `https://gitlab.com`
     - Project Identifier: `testgroup/testproject`
     - Access Token: `glpat-test-token`
   - Click Save
   - Verify success message
   - Refresh page and verify values persist

3. **Test as regular user**
   - Login as user without `manage_gitlab_configuration` permission
   - Open same work package
   - Go to GitLab tab
   - Verify "GitLab Setup" button does NOT appear

4. **Test API directly**
   ```bash
   # Get configuration (should auto-create)
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        http://localhost:3000/api/v3/projects/1/gitlab_configuration

   # Update configuration
   curl -X PATCH \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"gitlab_url":"https://gitlab.example.com","project_identifier":"test/project","access_token":"token"}' \
        http://localhost:3000/api/v3/projects/1/gitlab_configuration
   ```

## Verification Checklist

- [ ] Database migration completed successfully
- [ ] Frontend builds without errors
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] "GitLab Setup" button appears for users with permission
- [ ] Form toggles open/closed correctly
- [ ] Configuration can be saved
- [ ] Configuration can be updated
- [ ] Access token is not exposed in API responses
- [ ] Users without permission cannot see or modify configuration
- [ ] Success/error messages display correctly
- [ ] Configuration persists after page refresh

## Rollback Plan

If issues occur:

### 1. Disable UI (Quick)
```ruby
# Comment out the component in gitlab-tab.template.html
# <gitlab-setup [workPackage]="workPackage" />
```

### 2. Rollback Migration
```bash
bundle exec rake db:rollback STEP=1
# Or to specific version
bundle exec rake db:migrate:down VERSION=20250126000001
```

### 3. Remove Permission
Remove `manage_gitlab_configuration` permission from all roles in admin UI.

## Post-Deployment

### Monitor
- Check logs for any errors related to GitLabConfiguration
- Monitor API response times for the new endpoints
- Verify no N+1 queries or performance issues

### Documentation
- Update user documentation with screenshots
- Add to admin guide for permission management
- Document GitLab access token creation process

### Security Review
- Consider implementing encryption for access tokens
- Review audit logging requirements
- Plan for secure credential rotation

## Files Modified/Created Summary

### Backend
- Modified: `lib/open_project/gitlab_integration/engine.rb`
- Modified: `app/models/gitlab_configuration.rb`
- Modified: `db/migrate/20250126000001_create_gitlab_configurations.rb`
- Created: `lib/api/v3/gitlab_configurations/gitlab_configuration_representer.rb`
- Created: `lib/api/v3/gitlab_configurations/gitlab_configuration_by_project_api.rb`
- Created: `spec/requests/api/v3/gitlab_configuration_spec.rb`
- Created: `spec/features/gitlab_configuration_ui_spec.rb`

### Frontend
- Modified: `frontend/module/main.ts`
- Modified: `frontend/module/gitlab-tab/gitlab-tab.template.html`
- Created: `frontend/module/gitlab-setup/gitlab-setup.component.ts`
- Created: `frontend/module/gitlab-setup/gitlab-setup.template.html`
- Created: `frontend/module/gitlab-setup/gitlab-setup.component.sass`

### Documentation
- Created: `doc/gitlab_configuration_ui.md`
- Created: `GITLAB_CONFIGURATION_IMPLEMENTATION.md`
- Created: `DEPLOYMENT_CHECKLIST.md` (this file)

## Support

For issues or questions:
1. Check the implementation documentation in `doc/gitlab_configuration_ui.md`
2. Review the API tests for usage examples
3. Check browser console for frontend errors
4. Review Rails logs for backend errors

