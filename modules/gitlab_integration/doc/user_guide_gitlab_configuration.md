# GitLab Configuration UI - User Guide

## Overview

The GitLab Configuration UI allows project administrators to configure GitLab integration settings directly from the GitLab tab in work packages.

## Accessing the Configuration

1. Open any work package in a project with the GitLab module enabled
2. Click on the **GitLab** tab
3. At the top of the tab, you'll see the **GitLab Setup** button (only if you have permission)

## Using the Configuration Form

### Opening the Form

Click the **GitLab Setup** button to toggle the configuration form.

### Form Fields

The form contains three fields:

#### 1. GitLab URL
- **Description**: The base URL of your GitLab instance
- **Example**: `https://gitlab.com` or `https://gitlab.mycompany.com`
- **Required**: Yes

#### 2. Project Identifier
- **Description**: The full path to your GitLab project
- **Format**: `namespace/project-name` or `group/subgroup/project-name`
- **Example**: `myusername/my-project` or `myorg/team/project`
- **Required**: Yes
- **How to find**: Look at your GitLab project URL: `https://gitlab.com/myusername/my-project`

#### 3. Access Token
- **Description**: A GitLab Personal Access Token for API authentication
- **Type**: Password field (hidden)
- **Required**: Yes for full functionality
- **How to create**: See "Creating a GitLab Access Token" section below

### Saving the Configuration

1. Fill in all three fields
2. Click the **Save** button
3. Wait for the success message: "Configuration saved successfully!"

### Updating the Configuration

1. Click **GitLab Setup** to open the form
2. Modify any fields you want to update
3. Click **Save**

**Note**: The Access Token field will show asterisks (••••••••) if a token has been previously saved. You only need to enter a new token if you want to change it.

## Creating a GitLab Access Token

To use the GitLab integration, you need a Personal Access Token from GitLab:

### Steps:

1. **Log into GitLab**
   - Go to your GitLab instance (e.g., gitlab.com)

2. **Navigate to Access Tokens**
   - Click your profile picture (top right)
   - Select **Preferences** or **Settings**
   - In the left sidebar, click **Access Tokens**

3. **Create New Token**
   - Click **Add new token**
   - Enter a name (e.g., "OpenProject Integration")
   - Select an expiration date (or leave blank for no expiration)

4. **Select Scopes**
   - Check the following scopes:
     - ✅ `api` - Full API access
     - ✅ `read_api` - Read API
     - ✅ `read_repository` - Read repository
     - ✅ `write_repository` - Write repository (if creating merge requests)

5. **Create Token**
   - Click **Create personal access token**
   - **IMPORTANT**: Copy the token immediately (it won't be shown again)

6. **Paste into OpenProject**
   - Go back to OpenProject
   - Open the GitLab Setup form
   - Paste the token into the **Access Token** field
   - Click **Save**

## Permissions

### Who Can See the GitLab Tab?
Users with the **Show GitLab content** permission can view the GitLab tab and see issues and merge requests.

### Who Can Configure GitLab Settings?
Only users with the **Manage GitLab configuration** permission can see and use the GitLab Setup form. This is typically:
- Project Administrators
- Users with custom roles that include this permission

### Granting Permissions

**As an Administrator:**
1. Go to **Administration** → **Roles and permissions**
2. Select or create a role
3. Under **GitLab** module permissions, enable:
   - ✅ **Show GitLab content** (to view)
   - ✅ **Manage GitLab configuration** (to configure)
4. Save the role
5. Assign users to this role in the project

## Troubleshooting

### "GitLab Setup" Button Not Visible

**Possible causes:**
- You don't have the **Manage GitLab configuration** permission
- The GitLab module is not enabled for the project

**Solutions:**
- Contact your project administrator to grant you the permission
- Enable the GitLab module in Project Settings → Modules

### "Failed to save configuration" Error

**Possible causes:**
- Invalid GitLab URL format
- Missing required fields
- Network connectivity issues

**Solutions:**
- Ensure the GitLab URL is valid (starts with `http://` or `https://`)
- Fill in all three required fields
- Check your network connection
- Verify the GitLab instance is accessible

### "Failed to load GitLab configuration" Error

**Possible causes:**
- Network connectivity issues
- Server error
- Permission issues

**Solutions:**
- Refresh the page
- Check browser console for detailed errors
- Contact your system administrator

### Configuration Saves But GitLab Integration Doesn't Work

**Possible causes:**
- Incorrect GitLab URL
- Wrong Project Identifier format
- Invalid or expired Access Token
- Insufficient token permissions

**Solutions:**
- Verify the GitLab URL is correct (copy from your browser)
- Check the Project Identifier matches your GitLab project path exactly
- Create a new Access Token with all required scopes
- Test the token by accessing GitLab API directly

## Best Practices

### Security
- ⚠️ **Never share your Access Token** with others
- 🔄 **Rotate tokens regularly** (every 3-6 months)
- ⏰ **Set expiration dates** on tokens for better security
- 🔒 **Use tokens with minimal required scopes**

### Organization
- 📝 **Document which token is used** where
- 👥 **Use project or group tokens** when available (instead of personal)
- 🔍 **Regularly audit** who has configuration access

### Troubleshooting
- ✅ **Test the connection** after configuring
- 📋 **Keep a copy** of the Project Identifier
- 💾 **Backup configuration** before major changes

## Example Configurations

### GitLab.com (Public)
```
GitLab URL: https://gitlab.com
Project Identifier: myusername/myproject
Access Token: glpat-xxxxxxxxxxxxxxxxxxxx
```

### Self-Hosted GitLab
```
GitLab URL: https://gitlab.mycompany.com
Project Identifier: engineering/backend/api-service
Access Token: glpat-xxxxxxxxxxxxxxxxxxxx
```

### GitLab with Subgroups
```
GitLab URL: https://gitlab.com
Project Identifier: myorg/team-alpha/project-x
Access Token: glpat-xxxxxxxxxxxxxxxxxxxx
```

## Getting Help

If you encounter issues:

1. **Check the error message** - It usually indicates what's wrong
2. **Verify your inputs** - Especially the URL and Project Identifier
3. **Test your token** - Try accessing GitLab API with it directly
4. **Contact support** - Provide the error message and what you were doing

## Related Documentation

- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
- [Creating GitLab Personal Access Tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
- [OpenProject GitLab Integration Overview](../README.md)

