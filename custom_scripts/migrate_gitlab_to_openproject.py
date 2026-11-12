import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import unicodedata
import re
import time
import json
import os
import pytz

# --------------------------------------
# SECTION TO BE CONFIGURED FOR YOUR MIGRATION
# --------------------------------------
# GitLab configuration
# Replace with your GitLab personal access token and project ID
# Make sure the token has 'api' scope to access issues and notes
# You can create a personal access token in your GitLab profile settings under 'Access Tokens'.
GITLAB_TOKEN = ''  # Replace with your GitLab personal access token
GITLAB_PROJECT_ID = '4348'  # GitLab project ID to migrate issues from

# OpenProject Project ID to migrate issues into. To get the number ID just mouse over
# the projects list in the left sidebar and check the number in the URL.
OPENPROJECT_PROJECT_ID = '95'

# Debug control
DEBUG_ENABLED = False

# Attachments control - set to False to skip migrating images and attachments
MIGRATE_ATTACHMENTS = True

# Issue filtering by labels - set to None to migrate all issues, or provide a list of labels
# to only migrate issues that have at least one of the specified labels (OR logic).
# Example: FILTER_BY_LABELS = ["app: AVA", "app: Kaleidoscope", "priority: high"]
# With this example, any issue with "app: AVA" OR "app: Kaleidoscope" OR "priority: high" will be migrated.
# Set to None or empty list [] to migrate all issues (default behavior)
# FILTER_BY_LABELS = None  # or [] to migrate all, or ["label1", "label2"] to filter
FILTER_BY_LABELS = [
  "app: After Effects",
  "app: asap",
  "app: belt",
  "app: Bible Reader",
  "app: composer",
  "app: fcpx",
  "app feature: ASAP_shared_assets",
  "app feature: MAYA BELT_playblast",
  "app: hammer script",
  "app: houdini",
  "app: Maya",
  "app: nuke",
  "app: renderfarm",
  "app: Shotgrid",
  "app: surf",
  "app: wasap",
  "app: witt",
  "app: yeti",
  "app: Kaleidoscope",
  "app: AVA",
  "app: AVA_Archive_Plugin"
]

# Issue EXCLUSION filtering by labels - set to None to not exclude any issues,
# or provide a list of labels to EXCLUDE issues that have at least one of these labels (OR logic).
# Example: EXCLUDE_BY_LABELS = ["status: won't fix", "status: duplicate"]
# With this example, any issue with "status: won't fix" OR "status: duplicate" will be SKIPPED.
# This filter is applied AFTER FILTER_BY_LABELS, so you can combine both:
#   - FILTER_BY_LABELS includes issues with certain labels
#   - EXCLUDE_BY_LABELS then removes issues with unwanted labels from that set
# Set to None or empty list [] to not exclude any issues (default behavior)
EXCLUDE_BY_LABELS = []  # or [] to not exclude, or ["label1", "label2"] to exclude

# GitLab to OpenProject project mapping using GitLab labels, if not added/enabled to the list,
# the default OpenProject project ID will be used. Some project IDs are the following:
# MediaDev Support (Test) = 95
# Asap = 77
# Asap Belt = 78
# Kaleidoscope = 62
# Platform = 94
# AsapClient = 98
# AsapCore = 97
# To get the number ID of other available projects in OpenProject just mouse over the projects list in the left sidebar
# and check the number ID in the URL.
GITLAB_TO_OPENPROJECT_PROJECT = [
    {"gitlab_label": "dummy_entry", "openproject_project_id": OPENPROJECT_PROJECT_ID},
    {"gitlab_label": "app: After Effects", "openproject_project_id": 95},
    {"gitlab_label": "app: asap", "openproject_project_id": 105},
    # {"gitlab_label": "app: Kaleidoscope", "openproject_project_id": 135},
    # {"gitlab_label": "app: AVA", "openproject_project_id": 62},
    # {"gitlab_label": "app: AVA_Archive_Plugin", "openproject_project_id": 95},
    {"gitlab_label": "app: belt", "openproject_project_id": 105},
    {"gitlab_label": "app: Bible Reader", "openproject_project_id": 95},
    {"gitlab_label": "app: composer", "openproject_project_id": 95},
    {"gitlab_label": "app: fcpx", "openproject_project_id": 95},
    {"gitlab_label": "app feature: ASAP_shared_assets", "openproject_project_id": 105},
    {"gitlab_label": "app feature: MAYA BELT_playblast", "openproject_project_id": 105},
    {"gitlab_label": "app: hammer script", "openproject_project_id": 105},
    {"gitlab_label": "app: houdini", "openproject_project_id": 95},
    {"gitlab_label": "app: Maya", "openproject_project_id": 95},
    # {"gitlab_label": "app: monark", "openproject_project_id": 95},
    {"gitlab_label": "app: nuke", "openproject_project_id": 95},
    {"gitlab_label": "app: renderfarm", "openproject_project_id": 95},
    {"gitlab_label": "app: Shotgrid", "openproject_project_id": 95},
    {"gitlab_label": "app: surf", "openproject_project_id": 95},
    {"gitlab_label": "app: wasap", "openproject_project_id": 105},
    {"gitlab_label": "app: witt", "openproject_project_id": 95},
    {"gitlab_label": "app: yeti", "openproject_project_id": 95},
]

# GitLab to OpenProject priority mapping
# 426 = Very high
# 425 = High
# 424 = Medium
# 423 = Low
# 430 = Very low
GITLAB_TO_OPENPROJECT_PRIORITY = [
    {"gitlab_label": "priority: critical", "openproject_priority_id": 426},  # 426 = Very high
    {"gitlab_label": "priority: high", "openproject_priority_id": 425},  # 425 = High
    {"gitlab_label": "priority: normal", "openproject_priority_id": 424},  # 424 = Medium
    {"gitlab_label": "priority: low", "openproject_priority_id": 423},  # 423 = Low
]

# GitLab to OpenProject work package type mapping
GITLAB_TO_OPENPROJECT_TYPE = [
    {"gitlab_label": "type: bug", "openproject_type_name": "Bug"},
    {"gitlab_label": "type: enhancement", "openproject_type_name": "Feature"},
    {"gitlab_label": "type: feedback", "openproject_type_name": "Feature"},
    {"gitlab_label": "type: incident", "openproject_type_name": "Issue"},
    {"gitlab_label": "type: minor update", "openproject_type_name": "Feature"},
    {"gitlab_label": "type: pre-existing", "openproject_type_name": "Bug"},
    {"gitlab_label": "type: regression", "openproject_type_name": "Bug"},
]

# GitLab to OpenProject category mapping
# Categories in OpenProject are used to classify work packages by type of work or area
# Add your category mappings here based on your GitLab labels
GITLAB_TO_OPENPROJECT_CATEGORY = [
    {"gitlab_label": "app: After Effects", "openproject_category_name": "Adobe After Effects"},
    {"gitlab_label": "app: asap", "openproject_category_name": "Asap App"},
    {"gitlab_label": "app: AVA", "openproject_category_name": "AVA App"},
    {"gitlab_label": "app: AVA_Archive_Plugin", "openproject_category_name": "AVA App"},
    {"gitlab_label": "app: belt", "openproject_category_name": "Asap Belt"},
    {"gitlab_label": "app: Bible Reader", "openproject_category_name": "Bible Reader"},
    {"gitlab_label": "app: composer", "openproject_category_name": "Asap Belt"},
    {"gitlab_label": "app: fcpx", "openproject_category_name": "Final Cut Pro"},
    {"gitlab_label": "app feature: ASAP_shared_assets", "openproject_category_name": "Asap App"},
    {"gitlab_label": "app feature: MAYA BELT_playblast", "openproject_category_name": "Asap Belt"},
    {"gitlab_label": "app: hammer script", "openproject_category_name": "Asap Belt"},
    {"gitlab_label": "app: houdini", "openproject_category_name": "SideFX Houdini"},
    {"gitlab_label": "app: Kaleidoscope", "openproject_category_name": "Kaleidoscope App"},
    {"gitlab_label": "app: Maya", "openproject_category_name": "Autodesk Maya"},
    {"gitlab_label": "app: monark", "openproject_category_name": "Monark"},
    {"gitlab_label": "app: nuke", "openproject_category_name": "The Foundry Nuke"},
    {"gitlab_label": "app: renderfarm", "openproject_category_name": "Pixar's RenderMan"},
    {"gitlab_label": "app: Shotgrid", "openproject_category_name": "Autodesk Flow Production Tracking"},
    {"gitlab_label": "app: surf", "openproject_category_name": "Surf"},
    {"gitlab_label": "app: wasap", "openproject_category_name": "Asap App"},
    {"gitlab_label": "app: witt", "openproject_category_name": "Witt"},
    {"gitlab_label": "app: yeti", "openproject_category_name": "Yeti (Peregrine Labs)"},
]

# GitLab to OpenProject group mapping
# 69 = WHQ-AVS-Archivist
# 71 = WHQ-ART-TDSupport
# 72 = WHQ-AVS-TDSupport
# 73 = AUS-RVT-TDSupport
# 70 = AUS-RVT-Editors
# 68 = WHQ-ART-TeamCG
# 43 = WHQ-AVS-CGI
# 44 = WHQ-CD-MediaDevelopment
# 65 = WHQ-CD-MediaDevPlatform
# 53 = WHQ-CD-MediaDevTrackers
# 66 = WHQ-CD-MediaDevUserApps
GITLAB_TO_OPENPROJECT_GROUP = [
    {"gitlab_label": "dept_team: ART_CG", "openproject_group": "71"}, # 71 = WHQ-ART-TDSupport
    {"gitlab_label": "dept_team: AVS_ArchiveTeam", "openproject_group": "69"}, # 69 = WHQ-AVS-Archivist
    {"gitlab_label": "dept_team: AVS_AUS-VFX", "openproject_group": "73"}, # 73 = AUS-RVT-TDSupport
    {"gitlab_label": "dept_team: AVS_US-CGI", "openproject_group": "72"}, # 72 = WHQ-AVS-TDSupport
]

# Mapping for GitLab difficulty labels to OpenProject custom field 27 values
GITLAB_DIFFICULTY_TO_OP_VALUE = {
    "difficulty: 01": "Very small",
    "difficulty: 02": "Small",
    "difficulty: 03": "Medium",
    "difficulty: 04": "Large",
    "difficulty: 05": "Very large",
}

# Milestone to Version mapping configuration
# Month name to number mapping for milestone parsing
MONTH_NAME_TO_NUMBER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

# Labels that determine which app prefix to use for versions
# Order matters - first match wins (priority)
VERSION_APP_LABELS = [
    {"gitlab_label": "app: asap", "version_prefix": "Asap App"},
    {"gitlab_label": "app: belt", "version_prefix": "Asap Belt"},
]

# Custom field ID for Release version
RELEASE_VERSION_CUSTOM_FIELD_ID = 193

# GitLab status labels to OpenProject customField81 group mapping
# This maps specific GitLab status labels to OpenProject group IDs for customField81
GITLAB_STATUS_TO_CUSTOMFIELD81_GROUP = [
    {"gitlab_label": "status: waiting for CD feedback", "customfield81_group": 44},  # 44 = WHQ-CD-MediaDevelopment
    {"gitlab_label": "status: waiting for AVS feedback", "customfield81_group": 72},  # 43 = WHQ-AVS-TDSupport
]

# --------------------------------------
# END OF CONFIGURATION SECTION
# --------------------------------------

# ------------------------------------------------------------------
# Workpackage type to custom field id mapping
# This mapping is fixed and should not be changed
WORKPACKAGE_TYPE_TO_CUSTOMFIELD = {
    "Epic": 58,
    "Feature": 58,
    "User story": 58,
    "Change": 58,
    "Bug": 56,
    "Issue": 35,
}

# OpenProject work package types and their corresponding type IDs
# This mapping is fixed and should not be changed
OPENPROJECT_WORKPACKAGE_TYPES = [
    {"name": "Phase", "id": 243},
    {"name": "Gate", "id": 244},
    {"name": "Stage", "id": 227},
    {"name": "Milestone", "id": 226},
    {"name": "Epic", "id": 229},
    {"name": "Feature", "id": 228},
    {"name": "Bug", "id": 231},
    {"name": "User story", "id": 230},
    {"name": "Task", "id": 225},
    {"name": "Design", "id": 233},
    {"name": "AI", "id": 246},
    {"name": "Implementation", "id": 234},
    {"name": "Code maintenance", "id": 239},
    {"name": "Security", "id": 240},
    {"name": "Infrastructure", "id": 242},
    {"name": "Documentation", "id": 241},
    {"name": "Vacation", "id": 238},
    {"name": "Risk", "id": 235},
    {"name": "Issue", "id": 245},
    {"name": "Decision", "id": 236},
    {"name": "Change", "id": 237},
]

# GitLab URLs
# Replace with your GitLab instance URLs
GITLAB_API_URL = 'https://git.bethelservice.org/api/v4'
GITLAB_BASE_URL = 'https://git.bethelservice.org'

# OpenProject URLs
# Replace with your OpenProject instance URLs
OPENPROJECT_API_URL = 'https://openproject.bethelservice.org/api/v3'
# OpenProject Token
# Replace with your OpenProject API token
OPENPROJECT_TOKEN = ''

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
BACKOFF_FACTOR = 2

def debug_print(*args, **kwargs):
  """Print debug messages only if DEBUG is enabled"""
  if DEBUG_ENABLED:
    print("DEBUG:", *args, **kwargs)

def get_openproject_type_id_from_labels(gitlab_labels_list, enabled_type_ids=None):
    # Try to find a mapped type that is enabled for the project
    for mapping in GITLAB_TO_OPENPROJECT_TYPE:
        if mapping["gitlab_label"] in gitlab_labels_list:
            for t in OPENPROJECT_WORKPACKAGE_TYPES:
                if t["name"] == mapping["openproject_type_name"]:
                    if not enabled_type_ids or t["id"] in enabled_type_ids:
                        return t["id"]
    # Fallback to 'Feature' if enabled, else first enabled type
    if enabled_type_ids:
        for t in OPENPROJECT_WORKPACKAGE_TYPES:
            if t["name"] == "Feature" and t["id"] in enabled_type_ids:
                return t["id"]
        if enabled_type_ids:
            return enabled_type_ids[0]
    # Fallback to 'Feature' if no enabled_type_ids provided
    for t in OPENPROJECT_WORKPACKAGE_TYPES:
        if t["name"] == "Feature":
            return t["id"]
    return None

def get_openproject_project_id_from_labels(gitlab_labels_list):
    for mapping in GITLAB_TO_OPENPROJECT_PROJECT:
        if mapping["gitlab_label"] in gitlab_labels_list:
            return mapping["openproject_project_id"]
    return OPENPROJECT_PROJECT_ID  # Default to the configured project if no match

def get_openproject_group_from_labels(gitlab_labels_list):
    for mapping in GITLAB_TO_OPENPROJECT_GROUP:
        if mapping["gitlab_label"] in gitlab_labels_list:
            return mapping["openproject_group"]
    return None

def get_openproject_category_from_labels(gitlab_labels_list):
    """Get OpenProject category name from GitLab labels"""
    for mapping in GITLAB_TO_OPENPROJECT_CATEGORY:
        if mapping["gitlab_label"] in gitlab_labels_list:
            return mapping["openproject_category_name"]
    return None

def get_customfield81_group_from_labels(gitlab_labels_list):
    """Get OpenProject customField81 group ID from GitLab status labels"""
    for mapping in GITLAB_STATUS_TO_CUSTOMFIELD81_GROUP:
        if mapping["gitlab_label"] in gitlab_labels_list:
            return mapping["customfield81_group"]
    return None

def get_customfield_id_from_type(type_name):
    return WORKPACKAGE_TYPE_TO_CUSTOMFIELD.get(type_name)

def get_enabled_type_ids_for_project(project_id):
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}
    url = f"{OPENPROJECT_API_URL}/projects/{project_id}/types"
    resp = requests.get(url, headers=headers, auth=auth)
    resp.raise_for_status()
    data = resp.json()
    # The response is a collection with _embedded/elements
    types = data.get('_embedded', {}).get('elements', [])
    enabled_type_ids = [t['id'] for t in types if 'id' in t]
    if not enabled_type_ids:
        debug_print(f"No enabled types found for project {project_id}. Response: {data}")
    return enabled_type_ids

# --- Milestone to Version helpers ---
def parse_gitlab_milestone(milestone_title):
    """
    Parse a GitLab milestone title following the pattern "Month Year, Sprint N"

    Args:
        milestone_title: String like "November 2025, Sprint 1"

    Returns:
        Tuple of (year, month_number, sprint_number) or None if not matching the expected format
    """
    if not milestone_title:
        return None

    # Pattern: "Month Year, Sprint N"
    pattern = r'^(\w+)\s+(\d{4}),\s*Sprint\s+(\d+)$'
    match = re.match(pattern, milestone_title.strip())

    if not match:
        debug_print(f"Milestone '{milestone_title}' does not match expected format 'Month Year, Sprint N'")
        return None

    month_name = match.group(1)
    year = int(match.group(2))
    sprint = int(match.group(3))

    # Convert month name to number
    month_number = MONTH_NAME_TO_NUMBER.get(month_name)
    if not month_number:
        debug_print(f"Unknown month name '{month_name}' in milestone '{milestone_title}'")
        return None

    return (year, month_number, sprint)

def get_version_prefix_from_labels(gitlab_labels_list):
    """
    Get the version prefix based on GitLab labels.
    Returns the prefix for the first matching label (priority order).

    Args:
        gitlab_labels_list: List of GitLab labels

    Returns:
        Version prefix string like "Asap App" or "Asap Belt", or None if no matching label
    """
    if not gitlab_labels_list:
        return None

    for mapping in VERSION_APP_LABELS:
        if mapping["gitlab_label"] in gitlab_labels_list:
            return mapping["version_prefix"]

    return None

def build_version_name(year, month, sprint, prefix):
    """
    Build the OpenProject version name.

    Args:
        year: Year number (e.g., 2025)
        month: Month number (1-12)
        sprint: Sprint number

    Returns:
        Version name string like "Asap App v2025.11.1"
    """
    return f"{prefix} v{year}.{month}.{sprint}"

def get_or_create_version(project_id, version_name):
    """
    Get an existing version by name or create a new one.

    Args:
        project_id: OpenProject project ID
        version_name: Version name to find or create

    Returns:
        Version ID or None if creation failed
    """
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}

    # First, try to find the existing version
    versions_url = f"{OPENPROJECT_API_URL}/projects/{project_id}/versions"
    resp = requests.get(versions_url, headers=headers, auth=auth)

    if resp.status_code == 200:
        data = resp.json()
        versions = data.get('_embedded', {}).get('elements', [])
        for v in versions:
            if v.get('name') == version_name:
                debug_print(f"Found existing version '{version_name}' (id={v.get('id')})")
                return v.get('id')

    # Version not found, create it
    debug_print(f"Creating new version '{version_name}' in project {project_id}")
    create_url = f"{OPENPROJECT_API_URL}/versions"
    create_data = {
        "name": version_name,
        "_links": {
            "definingProject": {"href": f"/api/v3/projects/{project_id}"}
        },
        "status": "open"
    }

    create_resp = requests.post(create_url, headers=headers, json=create_data, auth=auth)

    if create_resp.status_code == 201:
        response_data = create_resp.json()
        version_id = response_data.get('id')
        debug_print(f"Created new version '{version_name}' (id={version_id})")
        return version_id
    else:
        print(f"WARNING: Failed to create version '{version_name}': {create_resp.status_code} - {create_resp.text}")
        return None

def get_version_info_from_milestone_and_labels(milestone, gitlab_labels_list):
    """
    Determine the version to assign based on GitLab milestone and labels.

    Args:
        milestone: GitLab milestone dict (or None)
        gitlab_labels_list: List of GitLab labels

    Returns:
        Tuple of (version_name, version_prefix) or (None, None) if no version should be assigned
    """
    # Check if milestone exists
    if not milestone:
        debug_print("No milestone assigned to this issue")
        return None, None

    milestone_title = milestone.get('title')
    if not milestone_title:
        debug_print("Milestone has no title")
        return None, None

    # Parse the milestone
    parsed = parse_gitlab_milestone(milestone_title)
    if not parsed:
        debug_print(f"Skipping milestone '{milestone_title}' - does not match expected format")
        return None, None

    year, month, sprint = parsed

    # Check if issue has one of the required labels
    version_prefix = get_version_prefix_from_labels(gitlab_labels_list)
    if not version_prefix:
        debug_print(f"Issue does not have 'app: asap' or 'app: belt' label - skipping version assignment")
        return None, None

    # Build the version name
    version_name = build_version_name(year, month, sprint, version_prefix)
    debug_print(f"Milestone '{milestone_title}' with label -> Version '{version_name}'")

    return version_name, version_prefix

# --- GitLab API helpers ---
def get_gitlab_issues(filter_labels=None, exclude_labels=None):
    """
    Fetch issues from GitLab project.

    Args:
        filter_labels: List of label names to filter by. If provided, only issues
                      that have at least one of these labels will be returned (OR logic).
                      If None or empty list, all issues are returned.
        exclude_labels: List of label names to exclude by. If provided, issues that have
                       at least one of these labels will be excluded (OR logic).
                       Applied AFTER filter_labels.

    Returns:
        List of GitLab issue dictionaries
    """
    headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}

    # If no filter labels, fetch all issues
    if not filter_labels or len(filter_labels) == 0:
        issues = []
        page = 1
        params = {'per_page': 100, 'page': page}

        while True:
            params['page'] = page
            resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            issues.extend(data)
            page += 1

        # Apply exclusion filter if provided
        if exclude_labels and len(exclude_labels) > 0:
            issues = apply_exclusion_filter(issues, exclude_labels)

        return issues

    # If filter labels provided, fetch issues for each label and combine (OR logic)
    # GitLab API with comma-separated labels uses AND logic, so we need to fetch separately
    print(f"Filtering issues by labels (OR logic): {', '.join(filter_labels)}")
    all_issues = {}  # Use dict to track unique issues by ID

    for label in filter_labels:
        print(f"  Fetching issues with label: {label}")
        page = 1

        while True:
            params = {
                'per_page': 100,
                'page': page,
                'labels': label
            }
            resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break

            # Add issues to dict using ID as key to avoid duplicates
            for issue in data:
                issue_id = issue.get('id')
                if issue_id and issue_id not in all_issues:
                    all_issues[issue_id] = issue

            page += 1

    issues_list = list(all_issues.values())
    print(f"  Total unique issues found (before exclusion): {len(issues_list)}")

    # Apply exclusion filter if provided
    if exclude_labels and len(exclude_labels) > 0:
        issues_list = apply_exclusion_filter(issues_list, exclude_labels)

    return issues_list

def apply_exclusion_filter(issues, exclude_labels):
    """
    Filter out issues that have any of the specified exclusion labels.

    Args:
        issues: List of GitLab issue dictionaries
        exclude_labels: List of label names to exclude

    Returns:
        Filtered list of issues (without issues that have exclusion labels)
    """
    if not exclude_labels or len(exclude_labels) == 0:
        return issues

    print(f"Excluding issues with labels (OR logic): {', '.join(exclude_labels)}")

    filtered_issues = []
    excluded_count = 0

    for issue in issues:
        issue_labels = issue.get('labels', [])
        # Check if issue has any of the exclusion labels
        has_exclusion_label = any(label in issue_labels for label in exclude_labels)

        if has_exclusion_label:
            excluded_count += 1
            debug_print(f"  Excluding issue '{issue.get('title')}' due to label match")
        else:
            filtered_issues.append(issue)

    print(f"  Excluded {excluded_count} issues, {len(filtered_issues)} remaining")
    return filtered_issues

def get_gitlab_issue_notes(issue_iid):
    headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}

    # Get basic notes/comments
    resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/notes", headers=headers)
    resp.raise_for_status()
    notes = resp.json()

    # Get resource label events
    try:
        resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/resource_label_events", headers=headers)
        resp.raise_for_status()
        label_events = resp.json()

        # Convert label events to note format
        for event in label_events:
            # Create a system note-like structure for label events
            system_note = {
                'id': f"label_event_{event.get('id')}",
                'author': event.get('user', {}),
                'created_at': event.get('created_at'),
                'updated_at': event.get('created_at'),
                'system': True,
                'noteable_id': issue_iid,
                'noteable_type': 'Issue'
            }

            # Format the body based on the action
            action = event.get('action')
            label = event.get('label', {}).get('name', 'unknown')

            if action == 'add':
                system_note['body'] = f"added ~{label} label"
            elif action == 'remove':
                system_note['body'] = f"removed ~{label} label"
            else:
                system_note['body'] = f"{action} ~{label} label"

            notes.append(system_note)

    except requests.exceptions.RequestException as e:
        debug_print(f"Could not fetch label events for issue {issue_iid}: {e}")

    # Get resource state events
    try:
        resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/resource_state_events", headers=headers)
        resp.raise_for_status()
        state_events = resp.json()

        # Convert state events to note format
        for event in state_events:
            system_note = {
                'id': f"state_event_{event.get('id')}",
                'author': event.get('user', {}),
                'created_at': event.get('created_at'),
                'updated_at': event.get('created_at'),
                'system': True,
                'noteable_id': issue_iid,
                'noteable_type': 'Issue'
            }

            # Format the body based on the state
            state = event.get('state')
            if state == 'closed':
                system_note['body'] = "closed"
            elif state == 'reopened':
                system_note['body'] = "reopened"
            else:
                system_note['body'] = f"changed state to {state}"

            notes.append(system_note)

    except requests.exceptions.RequestException as e:
        debug_print(f"Could not fetch state events for issue {issue_iid}: {e}")

    # Get resource milestone events
    try:
        resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/resource_milestone_events", headers=headers)
        resp.raise_for_status()
        milestone_events = resp.json()

        # Convert milestone events to note format
        for event in milestone_events:
            system_note = {
                'id': f"milestone_event_{event.get('id')}",
                'author': event.get('user', {}),
                'created_at': event.get('created_at'),
                'updated_at': event.get('created_at'),
                'system': True,
                'noteable_id': issue_iid,
                'noteable_type': 'Issue'
            }

            # Format the body based on the action
            action = event.get('action')
            milestone = event.get('milestone')

            if action == 'add' and milestone:
                milestone_title = milestone.get('title', 'unknown')
                system_note['body'] = f"added milestone {milestone_title}"
            elif action == 'remove' and milestone:
                milestone_title = milestone.get('title', 'unknown')
                system_note['body'] = f"removed milestone {milestone_title}"
            elif milestone:
                milestone_title = milestone.get('title', 'unknown')
                system_note['body'] = f"changed milestone to {milestone_title}"
            else:
                system_note['body'] = f"milestone {action}"

            notes.append(system_note)

    except requests.exceptions.RequestException as e:
        debug_print(f"Could not fetch milestone events for issue {issue_iid}: {e}")

    # Get resource weight events (if available)
    try:
        resp = requests.get(f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/resource_weight_events", headers=headers)
        resp.raise_for_status()
        weight_events = resp.json()

        # Convert weight events to note format
        for event in weight_events:
            system_note = {
                'id': f"weight_event_{event.get('id')}",
                'author': event.get('user', {}),
                'created_at': event.get('created_at'),
                'updated_at': event.get('created_at'),
                'system': True,
                'noteable_id': issue_iid,
                'noteable_type': 'Issue'
            }

            # Format the body based on the weight change
            weight = event.get('weight')
            if weight is not None:
                system_note['body'] = f"changed weight to {weight}"
            else:
                system_note['body'] = "removed weight"

            notes.append(system_note)

    except requests.exceptions.RequestException as e:
        debug_print(f"Could not fetch weight events for issue {issue_iid}: {e}")

    # Sort all notes chronologically by created_at
    notes.sort(key=lambda x: x.get('created_at', ''))

    debug_print(f"Fetched {len(notes)} total events for issue {issue_iid} (including notes, label events, state events, and milestone events)")

    return notes
# --- OpenProject API helpers ---
def test_openproject_token_and_project():
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {
        'Content-Type': 'application/json'
    }
    url = f"{OPENPROJECT_API_URL}/projects/{OPENPROJECT_PROJECT_ID}"
    resp = requests.get(url, headers=headers, auth=auth)
    print(f"Test project access status: {resp.status_code}")
    debug_print(f"Response: {resp.text}")
    resp.raise_for_status()
    return resp.json()

def is_customfield_in_schema(project_id, type_id, customfield_id):
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}
    url = f"{OPENPROJECT_API_URL}/projects/{project_id}/work_packages/form"
    data = {
        "_links": {
            "type": {"href": f"/api/v3/types/{type_id}"}
        },
        "subject": "Schema probe"
    }
    resp = requests.post(url, headers=headers, json=data, auth=auth)
    if resp.status_code == 200:
        schema = resp.json().get('_embedded', {}).get('schema', {})
        return f"customField{customfield_id}" in schema
    else:
        print(f"Schema fetch failed: {resp.text}")
        return False

def create_openproject_work_package(title, description, labels, gitlab_labels_list=None):
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {
        'Content-Type': 'application/json'
    }
    # Append labels at the end of the description if present
    modified_description = description
    if labels:
        modified_description = f"{description}\n\n---\n\n**GitLab Labels:**\n" + "\n".join(f"- {label}" for label in labels.split(", ")) if labels else description
    # Determine OpenProject priority from GitLab labels
    priority_id = None
    if gitlab_labels_list:
        for mapping in GITLAB_TO_OPENPROJECT_PRIORITY:
            if mapping['gitlab_label'] in gitlab_labels_list:
                priority_id = mapping['openproject_priority_id']
                break
    # Determine OpenProject type from GitLab labels
    project_id = get_openproject_project_id_from_labels(gitlab_labels_list or [])
    enabled_type_ids = get_enabled_type_ids_for_project(project_id)
    type_id = get_openproject_type_id_from_labels(gitlab_labels_list or [], enabled_type_ids)
    # Get type name for custom field logic
    type_name = None
    for t in OPENPROJECT_WORKPACKAGE_TYPES:
        if t["id"] == type_id:
            type_name = t["name"]
            break
    # Determine OpenProject project from GitLab labels
    project_id = get_openproject_project_id_from_labels(gitlab_labels_list or [])
    # Ensure type_id is enabled for the project
    enabled_type_ids = get_enabled_type_ids_for_project(project_id)
    if type_id not in enabled_type_ids:
        # Fallback to 'Feature' if available, else first enabled type
        fallback_type_id = None
        for t in OPENPROJECT_WORKPACKAGE_TYPES:
            if t["name"] == "Feature" and t["id"] in enabled_type_ids:
                fallback_type_id = t["id"]
                break
        if not fallback_type_id and enabled_type_ids:
            fallback_type_id = enabled_type_ids[0]
        type_id = fallback_type_id
        for t in OPENPROJECT_WORKPACKAGE_TYPES:
            if t["id"] == type_id:
                type_name = t["name"]
                break
    # Assign group to custom field if applicable and field exists in schema
    customfield_id = get_customfield_id_from_type(type_name) if type_name else None
    group_value = get_openproject_group_from_labels(gitlab_labels_list or [])

    # Determine OpenProject category from GitLab labels
    category_name = get_openproject_category_from_labels(gitlab_labels_list or [])

    data = {
        "_links": {
            "project": {"href": f"/api/v3/projects/{project_id}"}
        },
        "subject": title,
        "description": {"format": "markdown", "raw": modified_description},
        "type": {"href": f"/api/v3/types/{type_id}"}
    }

    # Set category if one was found from labels
    if category_name:
        # Fetch available categories for the project to get the category ID
        categories_url = f"{OPENPROJECT_API_URL}/projects/{project_id}/categories"
        categories_resp = requests.get(categories_url, headers=headers, auth=auth)
        category_id = None
        categories = []  # Initialize to avoid undefined variable warning
        if categories_resp.status_code == 200:
            categories_data = categories_resp.json()
            categories = categories_data.get('_embedded', {}).get('elements', [])
            for cat in categories:
                if cat.get('name') == category_name:
                    category_id = cat.get('id')
                    break

        if category_id:
            debug_print(f"Setting category to '{category_name}' (id={category_id})")
            data["_links"]["category"] = {"href": f"/api/v3/categories/{category_id}"}
        else:
            debug_print(f"Category '{category_name}' not found in project categories. Available categories: {[cat.get('name') for cat in categories]}")

    if priority_id:
        data["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
    if customfield_id and group_value:
        if is_customfield_in_schema(project_id, type_id, customfield_id):
            # Query allowed values for the custom field
            schema_url = f"{OPENPROJECT_API_URL}/projects/{project_id}/work_packages/form"
            schema_probe = {
                "_links": {"type": {"href": f"/api/v3/types/{type_id}"}},
                "subject": "Schema probe"
            }
            schema_resp = requests.post(schema_url, headers=headers, json=schema_probe, auth=auth)
            if schema_resp.status_code == 200:
                schema = schema_resp.json().get('_embedded', {}).get('schema', {})
                cf = schema.get(f'customField{customfield_id}', {})
                allowed_href = cf.get('_links', {}).get('allowedValues', {}).get('href')
                allowed_ids = []
                if allowed_href:
                    principals_url = f"https://openproject.bethelservice.org{allowed_href}" if allowed_href.startswith('/') else allowed_href
                    principals_resp = requests.get(principals_url, headers=headers, auth=auth)
                    if principals_resp.status_code == 200:
                        principals = principals_resp.json().get('_embedded', {}).get('elements', [])
                        allowed_ids = [str(p.get('id')) for p in principals]
                if str(group_value) in allowed_ids:
                    debug_print(f"Setting customField{customfield_id} = {group_value}")
                    data[f"customField{customfield_id}"] = {"href": f"/api/v3/groups/{int(group_value)}"}
                else:
                    debug_print(f"group_value {group_value} not allowed for customField{customfield_id}. Allowed: {allowed_ids}")
            else:
                debug_print(f"Could not fetch schema for customField{customfield_id}: {schema_resp.text}")
        else:
            debug_print(f"customField{customfield_id} not present in schema for type_id={type_id} in project_id={project_id}")
    # Assign customField81 for specific status labels
    customfield81_group = get_customfield81_group_from_labels(gitlab_labels_list or [])
    if customfield81_group and is_customfield_in_schema(project_id, type_id, 81):
        # Fetch allowed values for customField81 from schema
        auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
        headers = {'Content-Type': 'application/json'}
        url = f"{OPENPROJECT_API_URL}/projects/{project_id}/work_packages/form"
        schema_probe = {
            "_links": {"type": {"href": f"/api/v3/types/{type_id}"}},
            "subject": "Schema probe"
        }
        resp = requests.post(url, headers=headers, json=schema_probe, auth=auth)
        if resp.status_code == 200:
            schema = resp.json().get('_embedded', {}).get('schema', {})
            cf81 = schema.get('customField81', {})
            allowed_href = cf81.get('_links', {}).get('allowedValues', {}).get('href')
            allowed_ids = []
            if allowed_href:
                # Fetch allowed principals
                principals_url = f"https://openproject.bethelservice.org{allowed_href}" if allowed_href.startswith('/') else allowed_href
                principals_resp = requests.get(principals_url, headers=headers, auth=auth)
                if principals_resp.status_code == 200:
                    principals = principals_resp.json().get('_embedded', {}).get('elements', [])
                    allowed_ids = [p.get('id') for p in principals]
                    debug_print(f"Allowed principal IDs for customField81: {allowed_ids}")
                    if customfield81_group in allowed_ids:
                        debug_print(f"Setting customField81 = {customfield81_group}")
                        data["customField81"] = [{"href": f"/api/v3/groups/{customfield81_group}"}]
                    else:
                        debug_print(f"customField81 group {customfield81_group} not in allowed principals, skipping assignment.")
                else:
                    debug_print(f"Could not fetch allowed principals for customField81: {principals_resp.text}")
            else:
                debug_print(f"No allowedValues href for customField81 in schema.")
        else:
            debug_print(f"Could not fetch schema for customField81: {resp.text}")
    # Set difficulty custom field 27 if present (as _links/value for list fields)
    difficulty_value = get_difficulty_value_from_labels(gitlab_labels_list or [])
    customfield27_id = None
    if difficulty_value and is_customfield_in_schema(project_id, type_id, 27):
        # Fetch allowed values and find the matching custom option ID
        auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
        headers = {'Content-Type': 'application/json'}
        url = f"{OPENPROJECT_API_URL}/projects/{project_id}/work_packages/form"
        schema_probe = {
            "_links": {"type": {"href": f"/api/v3/types/{type_id}"}},
            "subject": "Schema probe"
        }
        resp = requests.post(url, headers=headers, json=schema_probe, auth=auth)
        if resp.status_code == 200:
            schema = resp.json().get('_embedded', {}).get('schema', {})
            cf27 = schema.get('customField27', {})
            allowed_values = cf27.get('_embedded', {}).get('allowedValues', [])
            # print(f"DEBUG: Allowed values for customField27: {[v.get('value') for v in allowed_values]}")
            for v in allowed_values:
                if v.get('value') == difficulty_value:
                    customfield27_id = v.get('id')
                    break
        else:
            debug_print(f"Could not fetch schema for customField27: {resp.text}")
        if customfield27_id:
            debug_print(f"Setting customField27 = {difficulty_value} (id={customfield27_id})")
            data["customField27"] = {"href": f"/api/v3/custom_options/{customfield27_id}"}
        else:
            debug_print(f"Could not find custom option ID for value '{difficulty_value}' in customField27 allowed values.")

    # --- Milestone-based Version Assignment ---
    # Check if the GitLab issue has a milestone and one of the required labels ("app: asap" or "app: belt")
    # If so, create/get the version and assign it to both Version field and Release version custom field (193)
    milestone_version_assigned = False
    gitlab_milestone = None

    # Try to get milestone from the 'issue' variable if available
    import inspect
    frame = inspect.currentframe()
    while frame:
        if 'issue' in frame.f_locals and isinstance(frame.f_locals['issue'], dict):
            gitlab_milestone = frame.f_locals['issue'].get('milestone')
            break
        frame = frame.f_back

    if gitlab_milestone:
        version_name, version_prefix = get_version_info_from_milestone_and_labels(gitlab_milestone, gitlab_labels_list or [])
        if version_name:
            # Get or create the version in OpenProject
            version_id = get_or_create_version(project_id, version_name)
            if version_id:
                debug_print(f"Setting Version to '{version_name}' (id={version_id})")
                data["_links"]["version"] = {"href": f"/api/v3/versions/{version_id}"}
                milestone_version_assigned = True

                # Also set Release version custom field (id 193) if it exists in schema
                if is_customfield_in_schema(project_id, type_id, RELEASE_VERSION_CUSTOM_FIELD_ID):
                    # For version custom fields, we need to find the allowed version by ID
                    # Fetch schema to check allowed values format
                    schema_url = f"{OPENPROJECT_API_URL}/projects/{project_id}/work_packages/form"
                    schema_probe = {
                        "_links": {"type": {"href": f"/api/v3/types/{type_id}"}},
                        "subject": "Schema probe"
                    }
                    schema_resp = requests.post(schema_url, headers=headers, json=schema_probe, auth=auth)
                    if schema_resp.status_code == 200:
                        schema = schema_resp.json().get('_embedded', {}).get('schema', {})
                        cf193 = schema.get(f'customField{RELEASE_VERSION_CUSTOM_FIELD_ID}', {})
                        cf_type = cf193.get('type', '')
                        debug_print(f"customField{RELEASE_VERSION_CUSTOM_FIELD_ID} type: {cf_type}")

                        # Set the custom field value - it expects a version reference
                        debug_print(f"Setting customField{RELEASE_VERSION_CUSTOM_FIELD_ID} (Release version) to '{version_name}' (id={version_id})")
                        data[f"customField{RELEASE_VERSION_CUSTOM_FIELD_ID}"] = {"href": f"/api/v3/versions/{version_id}"}
                    else:
                        debug_print(f"Could not fetch schema for customField{RELEASE_VERSION_CUSTOM_FIELD_ID}: {schema_resp.text}")
                else:
                    debug_print(f"customField{RELEASE_VERSION_CUSTOM_FIELD_ID} (Release version) not present in schema for type_id={type_id} in project_id={project_id}")
            else:
                debug_print(f"Failed to get or create version '{version_name}'")
    else:
        debug_print("No GitLab milestone found for this issue")

    # Set Version field if 'status: backlog' label is present (only if not already set by milestone)
    if not milestone_version_assigned and gitlab_labels_list and any('status: backlog' in label for label in gitlab_labels_list):
        # Fetch available versions for the project
        versions_url = f"{OPENPROJECT_API_URL}/projects/{project_id}/versions"
        versions_resp = requests.get(versions_url, headers=headers, auth=auth)
        version_id = None
        if versions_resp.status_code == 200:
            data_json = versions_resp.json()
            versions = data_json.get('_embedded', {}).get('elements', [])
            for v in versions:
                debug_print(f"Version found in project settings - {v.get('name')}")
                if v.get('name') == 'Product backlog':
                    version_id = v.get('id')
                    break
        if version_id:
            debug_print(f"Version assigned to Product backlog (id={version_id}).")
            # if "_links" not in data:
            #     data["_links"] = {}
            # data["_links"]["version"] = {"href": f"/api/v3/versions/{version_id}"}
            data["version"] = {"href": f"/api/v3/versions/{version_id}"}
        else:
            debug_print("'Product backlog' version not found in project versions.")
    # Set work package status based on GitLab issue state and WP type
    wp_status_id = None
    # Get gitlab_state directly from issue dict
    gitlab_state = None
    # Try to get state from the 'issue' argument if available
    # Fix: get state from the 'issue' parameter passed to this function
    if gitlab_labels_list is not None:
        # Try to get state from the global 'issue' variable if available
        import inspect
        frame = inspect.currentframe()
        while frame:
            if 'issue' in frame.f_locals and isinstance(frame.f_locals['issue'], dict):
                gitlab_state = frame.f_locals['issue'].get('state')
                break
            frame = frame.f_back
    # Fallback: Try to get state from labels if present
    if not gitlab_state and gitlab_labels_list:
        for label in gitlab_labels_list:
            if label.lower() == 'opened':
                gitlab_state = 'opened'
            elif label.lower() == 'closed':
                gitlab_state = 'closed'
    debug_print(f"gitlab_state={gitlab_state}")
    # Map status
    assignee = None
    # Try to get assignee from the 'issue' variable if available
    import inspect
    frame = inspect.currentframe()
    while frame:
        if 'issue' in frame.f_locals and isinstance(frame.f_locals['issue'], dict):
            assignee = frame.f_locals['issue'].get('assignee')
            debug_print(f"assignee={assignee}")
            break
        frame = frame.f_back
    if gitlab_state == 'closed':
        wp_status_id = 509  # Closed
        # Set assignee if found
        if assignee is not None:
            op_assignee_id = None
            auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
            headers = {'Content-Type': 'application/json'}
            url = f"{OPENPROJECT_API_URL}/projects/{project_id}/available_assignees"
            resp = requests.get(url, headers=headers, auth=auth)
            if resp.status_code == 200:
                assignable = resp.json().get('_embedded', {}).get('elements', [])
                def normalize(s):
                    if not s:
                        return ''
                    s = unicodedata.normalize('NFKD', s)
                    s = ''.join(c for c in s if not unicodedata.combining(c))
                    return s.lower().replace(',', '').replace('.', '').replace('@', '').replace(' ', '')
                assignee_username = normalize(assignee.get('username'))
                assignee_name = normalize(assignee.get('name'))
                for user in assignable:
                    user_login = normalize(user.get('login'))
                    user_name = normalize(user.get('name'))
                    user_first_last = normalize(f"{user.get('firstName', '')} {user.get('lastName', '')}")
                    user_last_first = normalize(f"{user.get('lastName', '')} {user.get('firstName', '')}")
                    if (
                        assignee_username and assignee_username in user_login
                    ) or (
                        assignee_name and (
                            assignee_name == user_name or
                            assignee_name == user_first_last or
                            assignee_name == user_last_first
                        )
                    ):
                        op_assignee_id = user.get('id')
                        break
            if op_assignee_id:
                debug_print(f"Assigning OpenProject assignee id {op_assignee_id} for GitLab assignee {assignee}")
                data['_links']['assignee'] = {'href': f'/api/v3/users/{op_assignee_id}'}
            else:
                print(f"WARNING: GitLab assignee {assignee} not found in OpenProject assignable users.")
    elif gitlab_state == 'opened':
        # If there is no assignee, leave status as default (New)
        if assignee is None:
            wp_status_id = None  # Do not assign, keep default
        else:
            # Check if assignee exists in OpenProject users/groups
            op_assignee_id = None
            auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
            headers = {'Content-Type': 'application/json'}
            url = f"{OPENPROJECT_API_URL}/projects/{project_id}/available_assignees"
            resp = requests.get(url, headers=headers, auth=auth)
            if resp.status_code == 200:
                assignable = resp.json().get('_embedded', {}).get('elements', [])
                def normalize(s):
                    if not s:
                        return ''
                    s = unicodedata.normalize('NFKD', s)
                    s = ''.join(c for c in s if not unicodedata.combining(c))
                    return s.lower().replace(',', '').replace('.', '').replace('@', '').replace(' ', '')
                assignee_username = normalize(assignee.get('username'))
                assignee_name = normalize(assignee.get('name'))
                for user in assignable:
                    user_login = normalize(user.get('login'))
                    user_name = normalize(user.get('name'))
                    user_first_last = normalize(f"{user.get('firstName', '')} {user.get('lastName', '')}")
                    user_last_first = normalize(f"{user.get('lastName', '')} {user.get('firstName', '')}")
                    if (
                        assignee_username and assignee_username in user_login
                    ) or (
                        assignee_name and (
                            assignee_name == user_name or
                            assignee_name == user_first_last or
                            assignee_name == user_last_first
                        )
                    ):
                        op_assignee_id = user.get('id')
                        break
            if op_assignee_id:
                debug_print(f"Assigning OpenProject assignee id {op_assignee_id} for GitLab assignee {assignee}")
                data['_links']['assignee'] = {'href': f'/api/v3/users/{op_assignee_id}'}
            else:
                print(f"WARNING: GitLab assignee {assignee} not found in OpenProject assignable users.")
            if type_name == 'Task':
                wp_status_id = 484  # In progress
            elif type_name == 'Bug' or type_name == 'Feature':
                wp_status_id = 483  # In development
            elif type_name == 'Issue':
                wp_status_id = 526  # In resolution
    if wp_status_id:
        debug_print(f"Setting work package status to {wp_status_id} based on GitLab state '{gitlab_state}' and type '{type_name}'.")
        data['_links']['status'] = {'href': f'/api/v3/statuses/{wp_status_id}'}
    resp = requests.post(f"{OPENPROJECT_API_URL}/work_packages", headers=headers, json=data, auth=auth)
    if resp.status_code != 201:
        print(f"Failed to create work package. Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        debug_print(f"type_id={type_id}, type_name={type_name}, enabled_type_ids={enabled_type_ids}, project_id={project_id}")
    resp.raise_for_status()
    return resp.json(), modified_description

def add_openproject_comment(work_package_id, comment, author_name=None, created_at=None):
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {
        'Content-Type': 'application/json'
    }
    if author_name and created_at:
        # Parse and format the date
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = dt.astimezone(pytz.timezone('US/Eastern')).strftime('%B %d, %Y at %I:%M %p')
        except Exception:
            formatted_date = created_at
        comment_text = f"**{author_name} wrote on {formatted_date}:**\n\n{comment}"
    elif author_name:
        comment_text = f"**{author_name}:** {comment}"
    else:
        comment_text = comment
    data = {"comment": {"raw": comment_text}}
    resp = requests.post(f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/activities", headers=headers, json=data, auth=auth)
    resp.raise_for_status()
    return resp.json()

def migrate_comment_images_and_attachments(comment_text, work_package_id):
    """Migrate images and attachments from GitLab comment text to OpenProject"""
    import base64
    import mimetypes
    import urllib.parse
    import json

    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}

    image_pattern_md = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_pattern_html = r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
    file_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

    matches_md = re.findall(image_pattern_md, comment_text)
    matches_html = re.findall(image_pattern_html, comment_text)
    matches_files = re.findall(file_link_pattern, comment_text)

    # Filter out image links from file links to avoid duplicates
    image_urls = set([url for _, url in matches_md] + [url for url in re.findall(image_pattern_html, comment_text)])
    matches_files = [(text, url) for text, url in matches_files if url not in image_urls and '/uploads/' in url]

    image_url_map = {}
    file_url_map = {}

    # Get existing attachments to avoid duplicates
    existing_attachments = get_existing_attachments(work_package_id)
    debug_print(f"Found {len(existing_attachments)} existing attachments for comment processing")

    def download_gitlab_file(file_url):
        """Download a file from GitLab using the proper API endpoint"""
        try:
            # Parse the GitLab upload URL to extract the file ID
            # URL format: /uploads/{hash}/{filename}
            if '/uploads/' in file_url:
                # Extract the file path from the URL
                url_parts = file_url.split('/uploads/')
                if len(url_parts) > 1:
                    file_path = url_parts[1]

                    # Try GitLab project uploads API endpoint
                    api_url = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/uploads/{file_path}"
                    headers_req = {'PRIVATE-TOKEN': GITLAB_TOKEN}
                    resp = requests.get(api_url, headers=headers_req)

                    if resp.status_code == 200:
                        debug_print(f"GitLab uploads API succeeded for {file_path}")
                        return resp
                    else:
                        debug_print(f"GitLab uploads API failed: {resp.status_code} - {resp.text}")

                        # Try alternative: direct file download from uploads
                        direct_url = f"{GITLAB_BASE_URL.rstrip('/')}/uploads/{file_path}"
                        resp = requests.get(direct_url, headers=headers_req)

                        if resp.status_code == 200 and not resp.headers.get('content-type', '').startswith('text/html'):
                            debug_print(f"Direct uploads URL succeeded for {file_path}")
                            return resp
                        else:
                            debug_print(f"Direct uploads URL also failed: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}")

            # Final fallback: try with authenticated session
            session = requests.Session()
            session.headers.update({
                'PRIVATE-TOKEN': GITLAB_TOKEN,
                'User-Agent': 'GitLab-Migration-Script',
                'Accept': 'image/*,*/*'
            })

            # Try to establish session by visiting sign-in page
            base_url = GITLAB_BASE_URL.rstrip('/')
            try:
                session.get(f"{base_url}/users/sign_in", timeout=10)
            except:
                pass  # Ignore sign-in page errors

            # Now try to download the file with session
            full_url = base_url + file_url if file_url.startswith('/') else file_url
            resp = session.get(full_url, allow_redirects=True, timeout=30)

            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                if not content_type.startswith('text/html'):
                    debug_print(f"Session-based download succeeded for {file_url}")
                    return resp
                else:
                    debug_print(f"Session download returned HTML instead of file. Content-Type: {content_type}")

        except Exception as e:
            debug_print(f"Exception in download_gitlab_file: {e}")

        return None

    # Process Markdown images
    for alt, url in matches_md:
        try:
            debug_print(f"Processing comment Markdown image: {url}")
            img_resp = download_gitlab_file(url)

            if img_resp and img_resp.status_code == 200:
                content_type = img_resp.headers.get('content-type', '')
                filename = url.split('/')[-1].split('?')[0]
                if not filename or '.' not in filename:
                    ext = mimetypes.guess_extension(content_type) or '.png'
                    filename = f"comment_image_{hash(url) % 10000}{ext}"

                # Check if attachment already exists
                existing_attachment_id = is_attachment_already_exists(filename, len(img_resp.content), existing_attachments)
                if existing_attachment_id:
                    debug_print(f"Comment image {filename} already exists in OpenProject (ID: {existing_attachment_id})")
                    op_url = f"{OPENPROJECT_API_URL}/attachments/{existing_attachment_id}/content"
                    image_url_map[url] = op_url
                    continue

                # Ensure proper content type
                if content_type == 'application/octet-stream':
                    guessed_type = mimetypes.guess_type(filename)[0]
                    if guessed_type:
                        content_type = guessed_type
                    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        content_type = f"image/{filename.split('.')[-1].lower()}"

                # Upload to OpenProject
                upload_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"
                metadata = {
                    'fileName': filename,
                    'description': f'Migrated comment image from GitLab: {alt or "Image"}'
                }

                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'file': (filename, img_resp.content, content_type)
                }

                up_resp = requests.post(upload_url, files=files, auth=auth)

                if up_resp.status_code == 201:
                    response_data = up_resp.json()
                    attachment_id = response_data.get('id')
                    if attachment_id:
                        op_url = f"{OPENPROJECT_API_URL}/attachments/{attachment_id}/content"
                        image_url_map[url] = op_url
                        debug_print(f"Uploaded comment image: {url} -> {op_url}")

                        # Update existing attachments list
                        existing_attachments.append({
                            'filename': filename,
                            'id': attachment_id,
                            'size': len(img_resp.content),
                            'description': metadata['description']
                        })
                else:
                    print(f"WARNING: Failed to upload comment image {filename}: {up_resp.status_code}")
            else:
                print(f"WARNING: Could not fetch comment image {url}")
        except Exception as e:
            print(f"WARNING: Error processing comment image {url}: {e}")

    # Process HTML images
    for url in matches_html:
        try:
            debug_print(f"Processing comment HTML image: {url}")
            img_resp = download_gitlab_file(url)

            if img_resp and img_resp.status_code == 200:
                content_type = img_resp.headers.get('content-type', '')
                filename = url.split('/')[-1].split('?')[0]
                if not filename or '.' not in filename:
                    ext = mimetypes.guess_extension(content_type) or '.png'
                    filename = f"comment_html_image_{hash(url) % 10000}{ext}"

                # Check if attachment already exists
                existing_attachment_id = is_attachment_already_exists(filename, len(img_resp.content), existing_attachments)
                if existing_attachment_id:
                    debug_print(f"Comment HTML image {filename} already exists in OpenProject (ID: {existing_attachment_id})")
                    op_url = f"{OPENPROJECT_API_URL}/attachments/{existing_attachment_id}/content"
                    image_url_map[url] = op_url
                    continue

                # Ensure proper content type
                if content_type == 'application/octet-stream':
                    guessed_type = mimetypes.guess_type(filename)[0]
                    if guessed_type:
                        content_type = guessed_type
                    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        content_type = f"image/{filename.split('.')[-1].lower()}"

                # Upload to OpenProject
                upload_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"
                metadata = {
                    'fileName': filename,
                    'description': 'Migrated comment image from GitLab'
                }

                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'file': (filename, img_resp.content, content_type)
                }

                up_resp = requests.post(upload_url, files=files, auth=auth)

                if up_resp.status_code == 201:
                    response_data = up_resp.json()
                    attachment_id = response_data.get('id')
                    if attachment_id:
                        op_url = f"{OPENPROJECT_API_URL}/attachments/{attachment_id}/content"
                        image_url_map[url] = op_url
                        debug_print(f"Uploaded comment HTML image: {url} -> {op_url}")

                        # Update existing attachments list
                        existing_attachments.append({
                            'filename': filename,
                            'id': attachment_id,
                            'size': len(img_resp.content),
                            'description': metadata['description']
                        })
                else:
                    print(f"WARNING: Failed to upload comment HTML image {filename}: {up_resp.status_code}")
            else:
                print(f"WARNING: Could not fetch comment HTML image {url}")
        except Exception as e:
            print(f"WARNING: Error processing comment HTML image {url}: {e}")

    # Process file attachments
    for text, url in matches_files:
        try:
            debug_print(f"Processing comment file attachment: {url}")
            file_resp = download_gitlab_file(url)

            if file_resp and file_resp.status_code == 200:
                content_type = file_resp.headers.get('content-type', '')
                filename = url.split('/')[-1].split('?')[0]
                if not filename or '.' not in filename:
                    ext = mimetypes.guess_extension(content_type) or ''
                    safe_text = re.sub(r'[^a-zA-Z0-9._-]', '_', text)[:50]
                    filename = f"comment_{safe_text}{ext}" if ext else f"comment_{safe_text}"

                # Check if attachment already exists
                existing_attachment_id = is_attachment_already_exists(filename, len(file_resp.content), existing_attachments)
                if existing_attachment_id:
                    debug_print(f"Comment file {filename} already exists in OpenProject (ID: {existing_attachment_id})")
                    op_url = f"{OPENPROJECT_API_URL}/attachments/{existing_attachment_id}/content"
                    file_url_map[url] = op_url
                    continue

                # Ensure proper content type
                if content_type == 'application/octet-stream' or not content_type:
                    guessed_type = mimetypes.guess_type(filename)[0]
                    if guessed_type:
                        content_type = guessed_type
                    else:
                        content_type = 'application/octet-stream'

                # Upload to OpenProject
                upload_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"
                metadata = {
                    'fileName': filename,
                    'description': f'Migrated comment file from GitLab: {text}'
                }

                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'file': (filename, file_resp.content, content_type)
                }

                up_resp = requests.post(upload_url, files=files, auth=auth)

                if up_resp.status_code == 201:
                    response_data = up_resp.json()
                    attachment_id = response_data.get('id')
                    if attachment_id:
                        op_url = f"{OPENPROJECT_API_URL}/attachments/{attachment_id}/content"
                        file_url_map[url] = op_url
                        debug_print(f"Uploaded comment file: {url} -> {op_url}")

                        # Update existing attachments list
                        existing_attachments.append({
                            'filename': filename,
                            'id': attachment_id,
                            'size': len(file_resp.content),
                            'description': metadata['description']
                        })
                else:
                    print(f"WARNING: Failed to upload comment file {filename}: {up_resp.status_code}")
            else:
                print(f"WARNING: Could not fetch comment file {url}")
        except Exception as e:
            print(f"WARNING: Error processing comment file {url}: {e}")

    # Replace URLs in comment text
    new_comment_text = comment_text

    # Replace Markdown image URLs
    def replace_md(match):
        alt, url = match.groups()
        return f'![{alt}]({image_url_map.get(url, url)})'
    new_comment_text = re.sub(image_pattern_md, replace_md, new_comment_text)

    # Replace HTML image src URLs
    new_comment_text = re.sub(r'(<img[^>]+src=["\'])([^"\'>]+)(["\'][^>]*>)',
                             lambda m: m.group(1) + image_url_map.get(m.group(2), m.group(2)) + m.group(3),
                             new_comment_text)

    # Replace file link URLs
    all_url_map = {**image_url_map, **file_url_map}
    def replace_file_links(match):
        text, url = match.groups()
        new_url = all_url_map.get(url, url)
        return f'[{text}]({new_url})'
    new_comment_text = re.sub(file_link_pattern, replace_file_links, new_comment_text)

    return new_comment_text

# --- Migration logic ---
def migrate():
    # Start timing the migration
    migration_start_time = time.time()

    # Load existing progress
    progress = load_progress()
    print(f"Loaded migration progress: {len(progress.get('migrated_issues', []))} issues already migrated")

    # Fetch issues with optional label filtering and exclusion
    issues = get_gitlab_issues(filter_labels=FILTER_BY_LABELS, exclude_labels=EXCLUDE_BY_LABELS)

    if FILTER_BY_LABELS and len(FILTER_BY_LABELS) > 0:
        print(f"Found {len(issues)} issues in GitLab with at least one of these labels (OR logic): {', '.join(FILTER_BY_LABELS)}")
    else:
        print(f"Found {len(issues)} issues in GitLab.")

    if EXCLUDE_BY_LABELS and len(EXCLUDE_BY_LABELS) > 0:
        print(f"(After excluding issues with labels: {', '.join(EXCLUDE_BY_LABELS)})")

    # Filter out already migrated issues
    print("Checking for already migrated issues...")
    remaining_issues = []
    for idx, issue in enumerate(issues):
        if (idx + 1) % 50 == 0:  # Print progress every 50 issues
            print(f"  Processed {idx + 1}/{len(issues)} issues...")

        existing_wp_id = issue_already_migrated(issue, progress)
        if existing_wp_id:
            print(f"Skipping already migrated issue: {issue['title']} (OpenProject ID: {existing_wp_id})")
        else:
            # Double-check by searching OpenProject for existing work package
            print(f"  Checking OpenProject for existing work package: {issue['title']}")
            existing_wp_id = get_existing_work_package_by_title(issue['title'])
            if existing_wp_id:
                print(f"Found existing work package in OpenProject: {issue['title']} (ID: {existing_wp_id})")
                add_migrated_issue(progress, issue, existing_wp_id)
                save_progress(progress)
            else:
                remaining_issues.append(issue)

    print(f"Filtering complete. {len(remaining_issues)} issues need to be migrated.")
    print(f"Migrating {len(remaining_issues)} remaining issues...")

    for idx, issue in enumerate(remaining_issues, start=1):
        title = issue['title']
        description = issue.get('description', '')
        labels_list = issue.get('labels', [])
        labels = ', '.join(labels_list)

        # Format author and creation date for the description
        author_name = issue.get('author', {}).get('name') or issue.get('author', {}).get('username', 'Unknown')
        created_at = issue.get('created_at')
        debug_print("Created at:", created_at)

        if created_at:
            try:
                # Parse UTC timestamp and keep in UTC instead of converting to local timezone
                dt_utc = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                # Keep in UTC timezone instead of converting to local
                formatted_date = f"{dt_utc.astimezone(pytz.timezone('US/Eastern')).strftime('%B %d, %Y at %I:%M %p')}"
            except Exception:
                formatted_date = created_at
        else:
            formatted_date = ''

        if author_name and formatted_date:
            description = f"**Created by {author_name} on {formatted_date}**\n\n" + description
        elif author_name:
            description = f"**Created by {author_name}.**\n\n" + description
        elif formatted_date:
            description = f"**Created on {formatted_date}.**\n\n" + description

        print(f"Migrating issue {idx}/{len(remaining_issues)}: {title}")

        try:
            # Create work package with retry logic
            print(f"  Creating work package...")
            wp, modified_description = retry_with_backoff(
                create_openproject_work_package,
                title, description, labels, labels_list
            )
            wp_id = wp['id']

            # Add to progress tracking
            add_migrated_issue(progress, issue, wp_id)
            save_progress(progress)
            print(f"Successfully created work package {wp_id}")

            # Migrate images and update description with retry logic
            if MIGRATE_ATTACHMENTS:
                try:
                    print(f"  Migrating images and attachments...")
                    retry_with_backoff(
                        migrate_images_and_update_description,
                        modified_description, wp_id,
                        HTTPBasicAuth('apikey', OPENPROJECT_TOKEN),
                        {'Content-Type': 'application/json'}
                    )
                    print(f"  Images and attachments migration completed")
                except Exception as e:
                    print(f"Warning: Failed to migrate images for work package {wp_id}: {e}")
            else:
                print(f"  Skipping images and attachments migration (MIGRATE_ATTACHMENTS=False)")

            # Migrate comments and activities with improved checking logic
            notes = get_gitlab_issue_notes(issue['iid'])
            if notes:
                print(f"  Processing {len(notes)} notes (comments and activities)...")

                # Group notes chronologically, combining activities between comments
                grouped_items = group_notes_chronologically(notes)
                print(f"  Grouped into {len(grouped_items)} items (comments and activity groups)")

                # Get existing OpenProject comments to avoid duplicates
                existing_op_comments = get_existing_openproject_comments(wp_id)
                print(f"  Found {len(existing_op_comments)} existing comments in OpenProject")

                items_migrated = 0
                for item in grouped_items:
                    if item['type'] == 'comment':
                        # Handle user comment
                        note = item['note']

                        # Check if comment already migrated using multiple methods
                        if comment_already_migrated(wp_id, note, progress):
                            debug_print(f"    Skipping already migrated comment (progress tracking)")
                            continue

                        # Also check if comment already exists in OpenProject by content
                        if is_comment_already_in_openproject(note, existing_op_comments):
                            debug_print(f"    Skipping comment that already exists in OpenProject")
                            # Add to progress tracking so we don't check again
                            add_migrated_comment(progress, wp_id, note)
                            save_progress(progress)
                            continue

                        try:
                            author_name = note.get('author', {}).get('name') or note.get('author', {}).get('username')
                            created_at = note.get('created_at')

                            # Process images and attachments in comment before adding it
                            if MIGRATE_ATTACHMENTS:
                                print(f"    Processing comment images and attachments...")
                                processed_comment = migrate_comment_images_and_attachments(note['body'], wp_id)
                            else:
                                print(f"    Skipping comment images and attachments (MIGRATE_ATTACHMENTS=False)")
                                processed_comment = note['body']

                            print(f"    Adding comment to OpenProject...")
                            retry_with_backoff(
                                add_openproject_comment,
                                wp_id, processed_comment, author_name, created_at
                            )

                            # Add to progress tracking
                            add_migrated_comment(progress, wp_id, note)
                            save_progress(progress)
                            items_migrated += 1
                            print(f"    Successfully migrated comment {items_migrated}")

                        except Exception as e:
                            print(f"Warning: Failed to migrate comment for work package {wp_id}: {e}")
                            continue

                    elif item['type'] == 'activities':
                        # Handle grouped activities
                        activities = item['activities']
                        if not activities:
                            continue

                        # Create a unique identifier for this activity group for progress tracking
                        activity_content = '\n'.join([act['text'] for act in activities])
                        activity_hash = hash(activity_content + str(item['created_at']))

                        # Check if this activity group has already been migrated
                        wp_activities = progress.get("migrated_comments", {}).get(str(wp_id), [])
                        if activity_hash in wp_activities:
                            debug_print(f"    Skipping already migrated activity group")
                            continue

                        # Format activities into a single comment
                        try:
                            # Parse and format the date from the first activity
                            created_at = item['created_at']
                            try:
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                formatted_date = dt.astimezone(pytz.timezone('US/Eastern')).strftime('%B %d, %Y at %I:%M %p')
                            except Exception:
                                formatted_date = created_at

                            # Determine if this is a single activity or grouped activities
                            is_grouped = len(activities) > 1

                            if is_grouped:
                                # For grouped activities: use "from" and include timestamps in individual activities
                                activity_comment = f"**Issue Activity from {formatted_date}:**\n\n"
                                activity_comment += '\n'.join([f"- {act['text']}" for act in activities])
                            else:
                                # For single activity: use "on" and remove timestamp from the activity
                                activity_comment = f"**Issue Activity on {formatted_date}:**\n\n"
                                # Re-format the single activity without timestamp
                                single_activity = format_gitlab_activity(activities[0]['note'], include_timestamp=False)
                                activity_comment += f"- {single_activity}"

                            print(f"    Adding {len(activities)} {'grouped' if is_grouped else 'single'} activit{'ies' if is_grouped else 'y'} to OpenProject...")
                            retry_with_backoff(
                                add_openproject_comment,
                                wp_id, activity_comment, None, None  # No specific author/date since it's a group
                            )

                            # Add to progress tracking
                            wp_activities.append(activity_hash)
                            if "migrated_comments" not in progress:
                                progress["migrated_comments"] = {}
                            progress["migrated_comments"][str(wp_id)] = wp_activities
                            save_progress(progress)

                            items_migrated += 1
                            print(f"    Successfully migrated activity group {items_migrated}")

                        except Exception as e:
                            print(f"Warning: Failed to migrate activity group for work package {wp_id}: {e}")
                            continue

                print(f"  Migration completed: {items_migrated} items migrated (comments and activity groups)")
            else:
                print(f"  No notes to migrate")

        except Exception as e:
            print(f"Error migrating issue '{title}': {e}")
            print("Continuing with next issue...")
            continue

    print("Migration complete.")
    print(f"Total migrated issues: {len(progress.get('migrated_issues', []))}")

    # Calculate and display total migration time
    migration_end_time = time.time()
    total_time_seconds = migration_end_time - migration_start_time

    # Format time in a readable way
    if total_time_seconds < 60:
        time_str = f"{total_time_seconds:.1f} seconds"
    elif total_time_seconds < 3600:
        minutes = int(total_time_seconds // 60)
        seconds = total_time_seconds % 60
        time_str = f"{minutes} minutes and {seconds:.1f} seconds"
    else:
        hours = int(total_time_seconds // 3600)
        minutes = int((total_time_seconds % 3600) // 60)
        seconds = total_time_seconds % 60
        time_str = f"{hours} hours, {minutes} minutes and {seconds:.1f} seconds"

    print(f"\n🕒 Total migration time: {time_str}")

    # Print summary
    if progress.get('migrated_issues'):
        print("\nMigration Summary:")
        for migrated in progress['migrated_issues'][-10:]:  # Show last 10
            print(f"  - {migrated['gitlab_title']} -> OpenProject ID {migrated['openproject_id']}")
        if len(progress['migrated_issues']) > 10:
            print(f"  ... and {len(progress['migrated_issues']) - 10} more")

def get_difficulty_value_from_labels(gitlab_labels_list):
    for key, value in GITLAB_DIFFICULTY_TO_OP_VALUE.items():
        for label in gitlab_labels_list:
            if key in label:
                return value
    return None

def migrate_images_and_update_description(description, work_package_id, auth, headers):
    import base64
    import mimetypes
    import urllib.parse
    import json  # Move json import to the top
    image_pattern_md = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_pattern_html = r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
    # Add pattern for file links: [filename](url)
    file_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

    matches_md = re.findall(image_pattern_md, description)
    matches_html = re.findall(image_pattern_html, description)
    # Find all file links (this will include images too, but we'll filter them)
    matches_files = re.findall(file_link_pattern, description)

    # Filter out image links from file links to avoid duplicates
    image_urls = set([url for _, url in matches_md] + [url for url in re.findall(image_pattern_html, description)])
    matches_files = [(text, url) for text, url in matches_files if url not in image_urls and '/uploads/' in url]

    image_url_map = {}
    file_url_map = {}

    # Get existing attachments to avoid duplicates
    existing_attachments = get_existing_attachments(work_package_id)
    print(f"Found {len(existing_attachments)} existing attachments in OpenProject")

    def download_gitlab_file(file_url):
        """Download a file from GitLab using the proper API endpoint"""
        try:
            # Parse the GitLab upload URL to extract the file ID
            # URL format: /uploads/{hash}/{filename}
            if '/uploads/' in file_url:
                # Extract the file path from the URL
                url_parts = file_url.split('/uploads/')
                if len(url_parts) > 1:
                    file_path = url_parts[1]

                    # Try GitLab project uploads API endpoint
                    # This is the correct endpoint for uploaded files
                    api_url = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/uploads/{file_path}"

                    headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
                    resp = requests.get(api_url, headers=headers)

                    if resp.status_code == 200:
                        debug_print(f"GitLab uploads API succeeded for {file_path}")
                        return resp
                    else:
                        debug_print(f"GitLab uploads API failed: {resp.status_code} - {resp.text}")

                        # Try alternative: direct file download from uploads
                        direct_url = f"{GITLAB_BASE_URL.rstrip('/')}/uploads/{file_path}"
                        resp = requests.get(direct_url, headers=headers)

                        if resp.status_code == 200 and not resp.headers.get('content-type', '').startswith('text/html'):
                            debug_print(f"Direct uploads URL succeeded for {file_path}")
                            return resp
                        else:
                            debug_print(f"Direct uploads URL also failed: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}")

            # Final fallback: try with authenticated session
            session = requests.Session()
            session.headers.update({
                'PRIVATE-TOKEN': GITLAB_TOKEN,
                'User-Agent': 'GitLab-Migration-Script',
                'Accept': 'image/*,*/*'
            })

            # Try to establish session by visiting sign-in page
            base_url = GITLAB_BASE_URL.rstrip('/')
            try:
                session.get(f"{base_url}/users/sign_in", timeout=10)
            except:
                pass  # Ignore sign-in page errors

            # Now try to download the file with session
            full_url = base_url + file_url if file_url.startswith('/') else file_url
            resp = session.get(full_url, allow_redirects=True, timeout=30)

            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                if not content_type.startswith('text/html'):
                    debug_print(f"Session-based download succeeded for {file_url}")
                    return resp
                else:
                    debug_print(f"Session download returned HTML instead of file. Content-Type: {content_type}")
                    # Try one more approach - extract any redirect or real URL from HTML
                    if 'href=' in resp.text:
                        debug_print(f"HTML response contains href, might be a redirect page")
            else:
                debug_print(f"Session download failed. Status: {resp.status_code}")

        except Exception as e:
            debug_print(f"Exception in download_gitlab_file: {e}")

        return None

    # Upload Markdown images with duplicate checking
    for alt, url in matches_md:
        try:
            debug_print(f"Processing Markdown image: {url}")
            img_resp = download_gitlab_file(url)

            if img_resp and img_resp.status_code == 200:
                content_type = img_resp.headers.get('content-type', '')
                debug_print(f"Image fetched successfully: {url}")
                debug_print(f"Actual content type: {content_type}")

                filename = url.split('/')[-1].split('?')[0]  # Remove query params
                if not filename or '.' not in filename:
                    # Generate a filename based on content type
                    ext = mimetypes.guess_extension(content_type) or '.png'
                    filename = f"image_{hash(url) % 10000}{ext}"

                # Check if attachment already exists
                existing_attachment_id = is_attachment_already_exists(filename, len(img_resp.content), existing_attachments)
                if existing_attachment_id:
                    debug_print(f"Image {filename} already exists in OpenProject (ID: {existing_attachment_id})")
                    # Use existing attachment URL
                    op_url = f"https://openproject.bethelservice.org/api/v3/attachments/{existing_attachment_id}/content"
                    image_url_map[url] = op_url
                    debug_print(f"Mapped existing image URL: {url} -> {op_url}")
                    continue

                # Ensure we have a proper content type
                if content_type == 'application/octet-stream':
                    # Try to get better content type from filename
                    guessed_type = mimetypes.guess_type(filename)[0]
                    if guessed_type:
                        content_type = guessed_type
                    elif filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                        content_type = 'image/jpeg'
                    elif filename.lower().endswith('.gif'):
                        content_type = 'image/gif'

                debug_print(f"File content length: {len(img_resp.content)}")
                debug_print(f"Using filename: {filename}")
                debug_print(f"Using content-type: {content_type}")

                # Try direct work package attachment upload with OpenProject's specific format
                upload_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"

                # OpenProject requires exactly two parts: metadata (JSON) and file (binary)
                # First part: metadata as JSON
                metadata = {
                    'fileName': filename,
                    'description': alt or 'Migrated image from GitLab'
                }

                # Create multipart form with the exact structure OpenProject expects
                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'file': (filename, img_resp.content, content_type)
                }

                debug_print(f"Uploading with OpenProject-specific format")
                debug_print(f"Metadata: {metadata}")
                debug_print(f"File: {(filename, len(img_resp.content), content_type)}")

                up_resp = requests.post(upload_url, files=files, auth=auth)

                if up_resp.status_code == 201:
                    debug_print(f"Image uploaded to OpenProject successfully.")
                    response_data = up_resp.json()
                    debug_print(f"Upload response: {response_data}")

                    # Use the permanent OpenProject attachment URL instead of downloadLocation
                    attachment_id = response_data.get('id')
                    if attachment_id:
                        # Use the permanent OpenProject API URL for attachments
                        op_url = f"{OPENPROJECT_API_URL}/attachments/{attachment_id}/content"
                        image_url_map[url] = op_url
                        debug_print(f"Mapped image URL: {url} -> {op_url}")

                        # Update existing attachments list for subsequent checks
                        existing_attachments.append({
                            'filename': filename,
                            'id': response_data.get('id'),
                            'size': len(img_resp.content),
                            'description': metadata['description']
                        })
                    else:
                        print("WARNING: No attachment ID found in response")
                else:
                    print(f"WARNING: OpenProject-specific format failed: {up_resp.status_code} - {up_resp.text}")
                    debug_print(f"All upload methods exhausted")
            else:
                print(f"WARNING: Could not fetch image {url}")
        except Exception as e:
            print(f"WARNING: Could not migrate image {url}: {e}")

    # Upload HTML images with duplicate checking (similar logic)
    for url in matches_html:
        try:
            debug_print(f"Processing HTML image: {url}")
            img_resp = download_gitlab_file(url)

            if img_resp and img_resp.status_code == 200:
                content_type = img_resp.headers.get('content-type', '')
                debug_print(f"Image fetched successfully: {url}")

                filename = url.split('/')[-1].split('?')[0]  # Remove query params
                if not filename or '.' not in filename:
                    # Generate a filename based on content type
                    ext = mimetypes.guess_extension(content_type) or '.png'
                    filename = f"image_{hash(url) % 10000}{ext}"

                # Check if attachment already exists
                existing_attachment_id = is_attachment_already_exists(filename, len(img_resp.content), existing_attachments)
                if existing_attachment_id:
                    debug_print(f"HTML Image {filename} already exists in OpenProject (ID: {existing_attachment_id})")
                    # Use existing attachment URL
                    op_url = f"https://openproject.bethelservice.org/api/v3/attachments/{existing_attachment_id}/content"
                    image_url_map[url] = op_url
                    debug_print(f"Mapped existing HTML image URL: {url} -> {op_url}")
                    continue

                # Ensure we have a proper content type
                if content_type == 'application/octet-stream':
                    # Try to get better content type from filename
                    guessed_type = mimetypes.guess_type(filename)[0]
                    if guessed_type:
                        content_type = guessed_type
                    elif filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                        content_type = 'image/jpeg'
                    elif filename.lower().endswith('.gif'):
                        content_type = 'image/gif'

                # Try direct work package attachment upload with OpenProject's specific format
                upload_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"

                # OpenProject requires exactly two parts: metadata (JSON) and file (binary)
                # First part: metadata as JSON
                metadata = {
                    'fileName': filename,
                    'description': 'Migrated image from GitLab'
                }

                # Create multipart form with the exact structure OpenProject expects
                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'file': (filename, img_resp.content, content_type)
                }

                debug_print(f"Uploading with OpenProject-specific format")
                debug_print(f"Metadata: {metadata}")
                debug_print(f"File: {(filename, len(img_resp.content), content_type)}")

                up_resp = requests.post(upload_url, files=files, auth=auth)

                if up_resp.status_code == 201:
                    debug_print(f"Image uploaded to OpenProject successfully.")
                    response_data = up_resp.json()
                    debug_print(f"Upload response: {response_data}")

                    # Use the permanent OpenProject attachment URL instead of downloadLocation
                    attachment_id = response_data.get('id')
                    if attachment_id:
                        # Use the permanent OpenProject API URL for attachments
                        op_url = f"{OPENPROJECT_API_URL}/attachments/{attachment_id}/content"
                        image_url_map[url] = op_url
                        debug_print(f"Mapped image URL: {url} -> {op_url}")

                        # Update existing attachments list for subsequent checks
                        existing_attachments.append({
                            'filename': filename,
                            'id': response_data.get('id'),
                            'size': len(img_resp.content),
                            'description': metadata['description']
                        })
                    else:
                        print("WARNING: No attachment ID found in response")
                else:
                    print(f"WARNING: OpenProject-specific format failed: {up_resp.status_code} - {up_resp.text}")
                    debug_print(f"All upload methods exhausted")
            else:
                print(f"WARNING: Could not fetch image {url}")
        except Exception as e:
            print(f"WARNING: Could not migrate image {url}: {e}")

    # Upload file attachments (non-images) with duplicate checking
    for text, url in matches_files:
        try:
            debug_print(f"Processing file attachment: {url}")
            file_resp = download_gitlab_file(url)

            if file_resp and file_resp.status_code == 200:
                content_type = file_resp.headers.get('content-type', '')
                debug_print(f"File fetched successfully: {url}")
                debug_print(f"Actual content type: {content_type}")

                filename = url.split('/')[-1].split('?')[0]  # Remove query params
                # filename = url.split('/')[-1]  # Use original filename
                if not filename or '.' not in filename:
                    # Generate a filename based on content type or use the link text
                    ext = mimetypes.guess_extension(content_type) or ''
                    safe_text = re.sub(r'[^a-zA-Z0-9._-]', '_', text)[:50]  # Sanitize filename
                    filename = f"{safe_text}{ext}" if ext else safe_text

                # Check if attachment already exists
                existing_attachment_id = is_attachment_already_exists(filename, len(file_resp.content), existing_attachments)
                if existing_attachment_id:
                    debug_print(f"File {filename} already exists in OpenProject (ID: {existing_attachment_id})")
                    # Use existing attachment URL
                    op_url = f"https://openproject.bethelservice.org/api/v3/attachments/{existing_attachment_id}/content"
                    file_url_map[url] = op_url
                    debug_print(f"Mapped existing file URL: {url} -> {op_url}")
                    continue

                # Ensure proper content type
                if content_type == 'application/octet-stream' or not content_type:
                    # Try to get better content type from filename
                    guessed_type = mimetypes.guess_type(filename)[0]
                    if guessed_type:
                        content_type = guessed_type
                    else:
                        content_type = 'application/octet-stream'

                debug_print(f"File content length: {len(file_resp.content)}")
                debug_print(f"Using filename: {filename}")
                debug_print(f"Using content-type: {content_type}")

                # Try direct work package attachment upload with OpenProject's specific format
                upload_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"

                # OpenProject requires exactly two parts: metadata (JSON) and file (binary)
                metadata = {
                    'fileName': filename,
                    'description': f'Migrated file from GitLab: {text}'
                }

                # Create multipart form with the exact structure OpenProject expects
                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'file': (filename, file_resp.content, content_type)
                }

                debug_print(f"Uploading file with OpenProject-specific format")
                debug_print(f"Metadata: {metadata}")
                debug_print(f"File: {(filename, len(file_resp.content), content_type)}")

                up_resp = requests.post(upload_url, files=files, auth=auth)

                if up_resp.status_code == 201:
                    debug_print(f"File uploaded to OpenProject successfully.")
                    response_data = up_resp.json()
                    debug_print(f"Upload response: {response_data}")

                    # Use the permanent OpenProject attachment URL instead of downloadLocation
                    attachment_id = response_data.get('id')
                    if attachment_id:
                        # Use the permanent OpenProject API URL for attachments
                        op_url = f"{OPENPROJECT_API_URL}/attachments/{attachment_id}/content"
                        file_url_map[url] = op_url
                        debug_print(f"Mapped file URL: {url} -> {op_url}")

                        # Update existing attachments list for subsequent checks
                        existing_attachments.append({
                            'filename': filename,
                            'id': response_data.get('id'),
                            'size': len(file_resp.content),
                            'description': metadata['description']
                        })
                    else:
                        print("WARNING: No attachment ID found in response")
                else:
                    print(f"WARNING: File upload failed: {up_resp.status_code} - {up_resp.text}")
                    debug_print(f"File upload exhausted")
            else:
                print(f"WARNING: Could not fetch file {url}")
        except Exception as e:
            print(f"WARNING: Could not migrate file {url}: {e}")

    # Replace Markdown image URLs
    def replace_md(match):
        alt, url = match.groups()
        return f'![{alt}]({image_url_map.get(url, url)})'
    new_description = re.sub(image_pattern_md, replace_md, description)

    # Replace HTML image src URLs
    new_description = re.sub(r'(<img[^>]+src=["\'])([^"\'>]+)(["\'][^>]*>)', lambda m: m.group(1) + image_url_map.get(m.group(2), m.group(2)) + m.group(3), new_description)

    # Replace file link URLs (merge both image and file URL maps)
    all_url_map = {**image_url_map, **file_url_map}
    def replace_file_links(match):
        text, url = match.groups()
        new_url = all_url_map.get(url, url)
        return f'[{text}]({new_url})'
    new_description = re.sub(file_link_pattern, replace_file_links, new_description)

    # Fetch current work package to get the updated lockVersion (attachments may have modified it)
    get_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}"
    get_resp = requests.get(get_url, headers=headers, auth=auth)

    if get_resp.status_code != 200:
        print(f"WARNING: Could not fetch current work package data: {get_resp.status_code} - {get_resp.text}")
        return new_description

    current_wp_data = get_resp.json()
    current_lock_version = current_wp_data.get('lockVersion')

    if current_lock_version is None:
        print("WARNING: Could not get lockVersion from work package data")
        return new_description

    # Update work package description with proper lockVersion
    patch_url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}"
    patch_headers = dict(headers)
    patch_headers['Content-Type'] = 'application/json'
    patch_payload = {
        "lockVersion": current_lock_version,
        "description": {"format": "markdown", "raw": new_description}
    }
    patch_resp = requests.patch(patch_url, headers=patch_headers, json=patch_payload, auth=auth)
    if patch_resp.status_code not in [200, 201]:
        print(f"WARNING: Could not update work package description: {patch_resp.status_code} - {patch_resp.text}")
        debug_print(f"Used lockVersion: {current_lock_version}")
    else:
        debug_print(f"Work package description updated successfully")

    return new_description

# Progress tracking file
PROGRESS_FILE = 'migration_progress.json'

def load_progress():
    """Load migration progress from file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load progress file: {e}")
    return {"migrated_issues": [], "migrated_comments": {}}

def save_progress(progress):
    """Save migration progress to file"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save progress: {e}")

def issue_already_migrated(issue, progress):
    """Check if an issue has already been migrated based on title and description"""
    for migrated in progress.get("migrated_issues", []):
        if (migrated.get("gitlab_title") == issue["title"] and
            migrated.get("gitlab_iid") == issue["iid"]):
            return migrated.get("openproject_id")
    return None

def get_existing_work_package_by_title(title):
    """Check if a work package with this title already exists in OpenProject"""
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}

    # Search for work packages with matching title
    search_url = f"{OPENPROJECT_API_URL}/work_packages"
    params = {
        'filters': json.dumps([{
            "subject": {
                "operator": "~",
                "values": [title]
            }
        }]),
        'pageSize': 10
    }

    try:
        resp = requests.get(search_url, headers=headers, auth=auth, params=params)
        if resp.status_code == 200:
            data = resp.json()
            elements = data.get('_embedded', {}).get('elements', [])
            for wp in elements:
                if wp.get('subject') == title:
                    return wp.get('id')
    except Exception as e:
        print(f"Warning: Could not search for existing work package: {e}")
    return None

def comment_already_migrated(work_package_id, note, progress):
    """Check if a comment has already been migrated"""
    wp_comments = progress.get("migrated_comments", {}).get(str(work_package_id), [])
    # We'll store a hash of the comment content to identify duplicates
    comment_hash = hash(note.get('body', '') + str(note.get('created_at', '')))
    return comment_hash in wp_comments  # Fixed: was checking incorrectly before

def get_existing_openproject_comments(work_package_id):
    """Get all existing comments from OpenProject work package"""
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}

    try:
        url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/activities"
        resp = requests.get(url, headers=headers, auth=auth)
        if resp.status_code == 200:
            data = resp.json()
            activities = data.get('_embedded', {}).get('elements', [])

            # Filter for comment activities and extract comment text
            comments = []
            for activity in activities:
                if activity.get('_type') == 'Activity::Comment':
                    comment_text = activity.get('comment', {}).get('raw', '')
                    created_at = activity.get('createdAt', '')
                    comments.append({
                        'text': comment_text,
                        'created_at': created_at,
                        'id': activity.get('id')
                    })
            return comments
    except Exception as e:
        print(f"Warning: Could not fetch existing comments for work package {work_package_id}: {e}")
    return []

def is_comment_already_in_openproject(gitlab_note, openproject_comments):
    """Check if a GitLab comment already exists in OpenProject based on content similarity"""
    gitlab_body = gitlab_note.get('body', '').strip()
    gitlab_author = gitlab_note.get('author', {}).get('name', '')

    for op_comment in openproject_comments:
        op_text = op_comment.get('text', '').strip()

        # Check if the GitLab comment content is contained in the OpenProject comment
        # (accounting for the formatting we add with author name and date)
        if gitlab_body in op_text and gitlab_author in op_text:
            return True

        # Also check for exact body match (in case formatting changed)
        if gitlab_body == op_text:
            return True

    return False

def get_existing_attachments(work_package_id):
    """Get all existing attachments from OpenProject work package"""
    auth = HTTPBasicAuth('apikey', OPENPROJECT_TOKEN)
    headers = {'Content-Type': 'application/json'}

    try:
        url = f"{OPENPROJECT_API_URL}/work_packages/{work_package_id}/attachments"
        resp = requests.get(url, headers=headers, auth=auth)
        if resp.status_code == 200:
            data = resp.json()
            attachments = data.get('_embedded', {}).get('elements', [])

            # Return list of attachment filenames and their details
            existing_files = []
            for attachment in attachments:
                existing_files.append({
                    'filename': attachment.get('fileName', ''),
                    'id': attachment.get('id'),
                    'size': attachment.get('fileSize', 0),
                    'description': attachment.get('description', '')
                })
            return existing_files
    except Exception as e:
        print(f"Warning: Could not fetch existing attachments for work package {work_package_id}: {e}")
    return []

def is_attachment_already_exists(filename, file_size, existing_attachments):
    """Check if an attachment with the same name and size already exists"""
    for existing in existing_attachments:
        if (existing['filename'] == filename and
            abs(existing['size'] - file_size) < 100):  # Allow small size differences
            return existing['id']
    return None

def retry_with_backoff(func, *args, **kwargs):
    """Retry a function with exponential backoff"""
    delay = RETRY_DELAY

    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [502, 503, 504, 429]:  # Server errors and rate limiting
                if attempt < MAX_RETRIES - 1:
                    print(f"Server error {e.response.status_code}, retrying in {delay} seconds... (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    delay *= BACKOFF_FACTOR
                    continue
            raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Connection error, retrying in {delay} seconds... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
                delay *= BACKOFF_FACTOR
                continue
            raise

    # If we get here, all retries failed
    raise Exception(f"Failed after {MAX_RETRIES} attempts")

def add_migrated_issue(progress, gitlab_issue, openproject_id):
    """Add an issue to the migrated list"""
    if "migrated_issues" not in progress:
        progress["migrated_issues"] = []

    progress["migrated_issues"].append({
        "gitlab_iid": gitlab_issue["iid"],
        "gitlab_title": gitlab_issue["title"],
        "openproject_id": openproject_id,
        "migrated_at": datetime.now().isoformat()
    })

def add_migrated_comment(progress, work_package_id, note):
    """Add a comment to the migrated list"""
    if "migrated_comments" not in progress:
        progress["migrated_comments"] = {}

    wp_id_str = str(work_package_id)
    if wp_id_str not in progress["migrated_comments"]:
        progress["migrated_comments"][wp_id_str] = []

    comment_hash = hash(note.get('body', '') + str(note.get('created_at', '')))
    progress["migrated_comments"][wp_id_str].append(comment_hash)

def format_gitlab_activity(note):
    """Format GitLab system activity into readable text"""
    if not note.get('system', False):
        body_skipped = note.get('body', '')
        return None

    author_name = note.get('author', {}).get('name') or note.get('author', {}).get('username', 'Unknown')
    body = note.get('body', '')
    created_at = note.get('created_at')

    # Format timestamp for activities
    timestamp_str = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            timestamp_str = f"{dt.astimezone(pytz.timezone('US/Eastern')).strftime('%m-%d-%Y %H:%M %p')} —"
        except Exception:
            timestamp_str = f"{created_at} —"

    # Parse different types of system activities
    if 'added' in body and 'label' in body:
        # Extract labels from "added ~label1 ~label2" format
        # Use regex to properly capture labels with spaces and special characters
        import re
        label_pattern = r'~([^~\s]+(?:\s+[^~\s]*)*)'
        labels = re.findall(label_pattern, body)
        if not labels:
            # Fallback: try to extract from the body text more carefully
            # Look for patterns like "added ~label text label"
            if '~' in body:
                # Split by ~ and take everything after it until the word "label" or end
                parts = body.split('~')
                if len(parts) > 1:
                    label_text = parts[1].strip()
                    # Remove trailing " label" if present
                    if label_text.endswith(' label'):
                        label_text = label_text[:-6].strip()
                    elif label_text.endswith('label'):
                        label_text = label_text[:-5].strip()
                    if label_text:
                        labels = [label_text]
        if labels:
            # return f"**{author_name}** added label{'s' if len(labels) > 1 else ''}: {', '.join(labels)}{timestamp_str}"
            return f"{timestamp_str} **{author_name}** added {', '.join(labels)}"

    elif 'removed' in body and 'label' in body:
        # Extract labels from "removed ~label1 ~label2" format
        # Use regex to properly capture labels with spaces and special characters
        import re
        label_pattern = r'~([^~\s]+(?:\s+[^~\s]*)*)'
        labels = re.findall(label_pattern, body)
        if not labels:
            # Fallback: try to extract from the body text more carefully
            # Look for patterns like "removed ~label text label"
            if '~' in body:
                # Split by ~ and take everything after it until the word "label" or end
                parts = body.split('~')
                if len(parts) > 1:
                    label_text = parts[1].strip()
                    # Remove trailing " label" if present
                    if label_text.endswith(' label'):
                        label_text = label_text[:-6].strip()
                    elif label_text.endswith('label'):
                        label_text = label_text[:-5].strip()
                    if label_text:
                        labels = [label_text]
        if labels:
            return f"{timestamp_str} **{author_name}** removed {', '.join(labels)}"

    elif 'changed the description' in body:
        return f"{timestamp_str} **{author_name}** changed the description"

    elif 'changed title from' in body:
        # Extract old and new titles
        if ' to ' in body:
            parts = body.split(' to ')
            if len(parts) >= 2:
                old_title = parts[0].replace('changed title from **', '').replace('**', '')
                new_title = parts[1].replace('**', '')
                return f"{timestamp_str} **{author_name}** changed title from \"{old_title}\" to \"{new_title}\""
        return f"{timestamp_str} **{author_name}** changed the title"

    elif 'milestone' in body:
        if 'changed milestone' in body:
            return f"{timestamp_str} **{author_name}** changed the milestone"
        elif 'added' in body:
            milestone = body.replace('added', '').replace('milestone', '').strip()
            return f"{timestamp_str} **{author_name}** added milestone: {milestone}"
        elif 'removed' in body:
            milestone = body.replace('removed', '').replace('milestone', '').strip()
            return f"{timestamp_str} **{author_name}** removed milestone: {milestone}"

    elif 'assigned to' in body:
        assignee = body.replace('assigned to', '').strip().replace('@', '')
        return f"{timestamp_str} **{author_name}** assigned to {assignee}"

    elif 'unassigned' in body:
        return f"{timestamp_str} **{author_name}** unassigned the issue"

    elif 'closed' in body:
        return f"{timestamp_str} **{author_name}** closed the issue"

    elif 'reopened' in body:
        return f"{timestamp_str} **{author_name}** reopened the issue"

    elif 'locked' in body:
        return f"{timestamp_str} **{author_name}** locked the discussion"

    elif 'unlocked' in body:
        return f"{timestamp_str} **{author_name}** unlocked the discussion"

    elif 'due date' in body:
        if 'changed due date' in body:
            return f"{timestamp_str} **{author_name}** changed the due date"
        elif 'removed due date' in body:
            return f"{timestamp_str} **{author_name}** removed the due date"
        elif 'added' in body:
            return f"{timestamp_str} **{author_name}** added a due date"

    elif 'moved from' in body or 'moved to' in body:
        return f"{timestamp_str} **{author_name}** moved the issue"

    elif 'mentioned in' in body:
        return f"{timestamp_str} **{author_name}** mentioned this issue elsewhere"

    # For any other system activity, return a generic format
    elif body.strip():
        return f"{timestamp_str} **{author_name}** {body}"

    return None

def group_notes_chronologically(notes):
    """Group notes chronologically, combining system activities between user comments"""
    # Sort all notes by creation date
    all_notes = sorted(notes, key=lambda x: x.get('created_at', ''))

    grouped_items = []
    current_activities = []

    for note in all_notes:
        if note.get('system', False):
            # This is a system activity
            activity_text = format_gitlab_activity(note)
            if activity_text:
                current_activities.append({
                    'text': activity_text,
                    'created_at': note.get('created_at'),
                    'author': note.get('author', {})
                })
        else:
            # This is a user comment
            # First, add any accumulated activities as a grouped comment
            if current_activities:
                grouped_items.append({
                    'type': 'activities',
                    'activities': current_activities,
                    'created_at': current_activities[0]['created_at']  # Use first activity's timestamp
                })
                current_activities = []

            # Add the user comment
            grouped_items.append({
                'type': 'comment',
                'note': note
            })

    # Don't forget any remaining activities at the end
    if current_activities:
        grouped_items.append({
            'type': 'activities',
            'activities': current_activities,
            'created_at': current_activities[0]['created_at']
        })

    return grouped_items

if __name__ == "__main__":
    # Test OpenProject token and project access before migration
    print("Testing OpenProject API token and project access...")
    try:
        test_openproject_token_and_project()
        print("OpenProject API token and project access are valid. Proceeding with migration.")
    except Exception as e:
        print(f"OpenProject API token or project access failed: {e}")
        exit(1)
    migrate()
