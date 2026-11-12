# Encryption Issue Fix

## Problem

When running the rake task to configure GitLab integration:

```bash
bundle exec rake gitlab_integration:configure[project,url,id,token]
```

The following error occurred:

```
ActiveRecord::Encryption::Errors::Configuration: Missing Active Record encryption credential: active_record_encryption.primary_key
```

## Root Cause

The `GitlabConfiguration` model was using Rails 7+ `encrypts` feature:

```ruby
encrypts :access_token, deterministic: false
```

This requires encryption keys to be configured in `config/credentials.yml.enc` or environment variables:
- `active_record_encryption.primary_key`
- `active_record_encryption.deterministic_key`
- `active_record_encryption.key_derivation_salt`

These were not set up in the OpenProject installation, causing the error.

## Solution

Removed the application-level encryption and instead store tokens as plain text in the database with a recommendation to use database-level encryption.

### Changes Made

1. **Updated `app/models/gitlab_configuration.rb`**
   - Removed `encrypts :access_token, deterministic: false`
   - Added comments recommending database encryption at rest
   - Tokens now stored as plain text in the database

2. **Updated Documentation**
   - `QUICK_START.md` - Added security notes about database encryption
   - `doc/CREATE_MERGE_REQUEST_FEATURE.md` - Updated security section
   - `IMPLEMENTATION_SUMMARY.md` - Updated feature descriptions

## Security Recommendations

Since tokens are now stored as plain text in the database, the following security measures are recommended:

### For Development
- Restrict database access to localhost only
- Use strong database passwords
- Don't commit database files to version control

### For Production
- **Enable database encryption at rest** (supported by PostgreSQL, MySQL, etc.)
- Use database connection encryption (SSL/TLS)
- Implement proper database access controls
- Regular security audits
- Token rotation policies
- Restrict database access to authorized personnel only
- Ensure database backups are encrypted
- Consider using a secrets management system (HashiCorp Vault, AWS Secrets Manager, etc.)

## Alternative Solutions (For Future Enhancement)

If application-level encryption is required, here are some options:

### Option 1: Set up Rails Encryption Keys

Generate encryption keys:

```bash
bundle exec rails db:encryption:init
```

Add to credentials:

```bash
EDITOR="nano" bundle exec rails credentials:edit
```

Add:
```yaml
active_record_encryption:
  primary_key: [generated key]
  deterministic_key: [generated key]
  key_derivation_salt: [generated salt]
```

### Option 2: Use attr_encrypted Gem

Add to Gemfile:
```ruby
gem 'attr_encrypted'
```

Update model:
```ruby
attr_encrypted :access_token,
               key: Rails.application.secret_key_base,
               mode: :per_attribute_iv_and_salt
```

Update migration to add encryption columns:
```ruby
add_column :gitlab_configurations, :encrypted_access_token, :string
add_column :gitlab_configurations, :encrypted_access_token_iv, :string
```

### Option 3: Use OpenProject's Existing Secret Storage

If OpenProject has an existing pattern for storing secrets (like API keys, tokens, etc.), follow that pattern instead.

## Testing

After the fix, the rake task should work:

```bash
# Configure
bundle exec rake gitlab_integration:configure[myproject,https://gitlab.com,group/project,glpat-xxxxx]

# Verify
bundle exec rake gitlab_integration:show[myproject]

# Should output:
# GitLab Configuration for 'My Project':
#   GitLab URL: https://gitlab.com
#   GitLab Project: group/project
#   Access Token: [CONFIGURED]
#   Status: ✓ Configured
```

## Migration Path

Existing installations don't need any migration since the feature is new. The database schema remains the same (text column for access_token).

If encryption was previously enabled and tokens were encrypted, a data migration would be needed, but since this is the initial release, no migration is necessary.

## Files Modified

1. `app/models/gitlab_configuration.rb` - Removed encryption
2. `QUICK_START.md` - Updated security notes
3. `doc/CREATE_MERGE_REQUEST_FEATURE.md` - Updated security section
4. `IMPLEMENTATION_SUMMARY.md` - Updated descriptions

## Conclusion

The rake task and configuration should now work without requiring additional encryption key setup. For production deployments, database-level encryption at rest is strongly recommended.

