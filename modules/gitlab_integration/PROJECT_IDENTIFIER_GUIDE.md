# Project Identifier vs Project ID - Quick Reference

## Understanding the Difference

OpenProject has **TWO** different identifiers for projects:

### 1. Project ID (Numeric)
- **Type**: Integer (bigint in database)
- **Example**: `1`, `2`, `123`
- **Database column**: `projects.id`
- **Where used**: Database foreign keys, internal references
- **URL example**: `http://localhost:3000/projects/1`

### 2. Project Identifier (String)
- **Type**: String (character varying in database)
- **Example**: `demo-project`, `scrum-project`, `my-awesome-project`
- **Database column**: `projects.identifier`
- **Where used**: URLs, slugs, human-readable references
- **URL example**: `http://localhost:3000/projects/demo-project`

## For GitLab Integration Configuration

**Use the Project Identifier (STRING)**

❌ **WRONG** - Using numeric ID:
```bash
rake gitlab_integration:configure[1,https://gitlab.com,group/project,token]
```

✅ **CORRECT** - Using string identifier:
```bash
rake gitlab_integration:configure[demo-project,https://gitlab.com,group/project,token]
```

## How to Find Your Project Identifier

### Method 1: Check the URL
When viewing a project in OpenProject, the URL shows the identifier:
```
http://localhost:3000/projects/demo-project
                                ^^^^^^^^^^^^
                                This is the identifier
```

### Method 2: Use Rails Console
```bash
bundle exec rails console
```

```ruby
# List all projects with their identifiers
Project.all.each do |p|
  puts "ID: #{p.id.to_s.rjust(3)} | Identifier: #{p.identifier.ljust(20)} | Name: #{p.name}"
end

# Output example:
# ID:   1 | Identifier: demo-project         | Name: Demo project
# ID:   2 | Identifier: scrum-project        | Name: Scrum project
```

### Method 3: Use Rails Runner (One-liner)
```bash
bundle exec rails runner "Project.all.each { |p| puts '#{p.identifier} => #{p.name}' }"
```

Output:
```
demo-project => Demo project
scrum-project => Scrum project
```

### Method 4: Check Project Settings
1. Open the project in OpenProject
2. Go to **Project Settings** → **Information**
3. Look for the **Identifier** field

## Why Use Identifier Instead of ID?

1. **Human-readable**: `demo-project` is easier to remember than `1`
2. **Stable**: Identifiers don't change; IDs might differ across environments
3. **URL-friendly**: Identifiers are used in URLs
4. **Consistent**: OpenProject's convention throughout the application

## The Rake Task Explained

```bash
rake gitlab_integration:configure[PROJECT_IDENTIFIER,GITLAB_URL,GITLAB_PROJECT,TOKEN]
```

### Parameter Breakdown:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `PROJECT_IDENTIFIER` | OpenProject project identifier (string) | `demo-project` |
| `GITLAB_URL` | GitLab instance URL | `https://gitlab.com` |
| `GITLAB_PROJECT` | GitLab project path or numeric ID | `group/project` or `6220` |
| `TOKEN` | GitLab access token | `glpat-xxxxx...` |

**Note**: The GitLab project parameter CAN be numeric (like `6220`) because that's GitLab's identifier format, but the OpenProject project parameter must be the string identifier!

## Database Schema

The `gitlab_configurations` table:

```ruby
create_table "gitlab_configurations" do |t|
  t.bigint "project_id", null: false    # Foreign key to projects.id (numeric)
  t.string "gitlab_url", null: false
  t.string "project_identifier"          # GitLab project (not OpenProject!)
  t.text "access_token"
  t.timestamps
end
```

The `project_id` column stores the numeric ID, but the rake task finds it by looking up the project using the identifier:

```ruby
project = Project.find_by(identifier: 'demo-project')
config.project = project  # This sets project_id automatically
```

## Common Mistakes

### ❌ Mistake 1: Using numeric ID
```bash
rake gitlab_integration:configure[1,https://gitlab.com,...]
# Error: Project with identifier '1' not found
```

### ❌ Mistake 2: Confusing OpenProject and GitLab identifiers
```bash
# Wrong parameter order
rake gitlab_integration:configure[6220,https://gitlab.com,demo-project,token]
```

### ✅ Correct Usage
```bash
# OpenProject identifier first, then GitLab project
rake gitlab_integration:configure[demo-project,https://gitlab.com,6220,token]
```

## Quick Test

To verify your project identifier before configuring:

```bash
bundle exec rails runner "p = Project.find_by(identifier: 'demo-project'); puts p ? 'Found: ' + p.name : 'Not found'"
```

If it says "Found: Demo project", you have the right identifier!

## Summary

**For the rake task, always use the string identifier from the `projects.identifier` column, NOT the numeric ID from `projects.id`.**

When in doubt, check the project URL or list all projects to find the correct identifier.

