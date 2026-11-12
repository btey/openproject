import json
import requests
import base64
import os
from ldap3 import Server, Connection, ALL, SUBTREE


# LDAP and API server configuration
LDAP_SERVER = "ldap://bethel.jw.org"
LDAP_USER = "usalinuxldap@bethel.jw.org"
LDAP_PASSWORD = base64.b64decode(os.getenv("LDAP_PASSWORD")) if os.getenv("LDAP_PASSWORD") else None
BASE_DN = "dc=bethel,dc=jw,dc=org"
GROUP_OBJECT_CLASS = "*"

API_SERVER = "https://openproject.bethelservice.org"
API_USERNAME = "apikey"  # Fixed username for Basic Auth
API_PASSWORD = os.getenv("ADMIN_OP_TOKEN")  # The API token serves as the password

# Encode credentials in Base64 for Basic Authentication
auth_string = f"{API_USERNAME}:{API_PASSWORD}"
auth_bytes = base64.b64encode(auth_string.encode("utf-8"))
auth_header = auth_bytes.decode("utf-8")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {auth_header}"
}

def fetch_groups():
    """Fetch the list of groups from the API."""
    url = f"{API_SERVER}/api/v3/groups"
    response = requests.get(url, headers=HEADERS, verify=False)

    if response.status_code == 200:
        data = response.json()
        groups = []
        for group in data["_embedded"]["elements"]:
            groups.append({
                "id": group["id"],
                "name": group["name"]
            })
        return groups
    else:
        print(f"Failed to fetch groups. Response: {response.text}")
        return []

def check_group_exists(ldap_connection, group_name):
    """Check if a group exists in LDAP."""
    search_filter = f"(&(objectClass={GROUP_OBJECT_CLASS})(cn={group_name}))"
    ldap_connection.search(BASE_DN, search_filter, SUBTREE, attributes=["cn"])

    if ldap_connection.entries:
        print(f"Group {group_name} found in Active Directory.")
        return True
    else:
        print(f"Group {group_name} not found in Active Directory. Skipping...")
        return False

def fetch_group_members(ldap_connection, group_name):
    """Fetch members of a given LDAP group."""
    search_filter = f"(&(objectClass={GROUP_OBJECT_CLASS})(cn={group_name}))"
    ldap_connection.search(BASE_DN, search_filter, SUBTREE, attributes=["member"])

    if not ldap_connection.entries:
        print(f"Group {group_name} not found or has no members.")
        return []

    members = []
    for entry in ldap_connection.entries:
        members.extend(entry.member.values)
    print(f"Found {len(members)} members in group {group_name}.")
    return members


def fetch_user_details(ldap_connection, user_dn):
    """Fetch user details from LDAP."""
    ldap_connection.search(user_dn, "(objectClass=person)", SUBTREE, attributes=["uid", "mail", "cn", "sn", "givenName"])

    if not ldap_connection.entries:
        print(f"User {user_dn} not found.")
        return None

    entry = ldap_connection.entries[0]
    return {
        "uid": entry.uid.value,
        "email": entry.mail.value,
        "full_name": f"{entry.givenName.value} {entry.sn.value}"
    }

def fetch_user_id(full_name):
    """Fetch user ID from the API using the email."""
    filters = '[{"name":{"operator":"=","values":["' + full_name + '"]}}]'
    url = f"{API_SERVER}/api/v3/users?filters={filters}"
    response = requests.get(url, headers=HEADERS, verify=False)

    if response.status_code == 200:
        data = response.json()
        if "total" in data and data["total"] > 0:
            return data["_embedded"]["elements"][0]["id"]  # Assuming first match is correct
        else:
            print(f"No user found with email: {full_name}")
    else:
        print(f"Failed to fetch user ID for email {full_name}. Response: {response.text}")
    return None

def update_group_members(group_id, group_name, member_ids):
    """Update group members via API."""
    # Remove duplicates
    unique_member_ids = list(set(member_ids))
    members = [{"href": f"/api/v3/users/{uid}"} for uid in unique_member_ids]
    payload = {
        "name": group_name,
        "_links": {
            "members": members
        }
    }
    url = f"{API_SERVER}/api/v3/groups/{group_id}"
    response = requests.patch(url, headers=HEADERS, data=json.dumps(payload), verify=False)

    if response.status_code == 200:
        print(f"Successfully updated group {group_name} (ID: {group_id}).")
    else:
        print(f"Failed to update group {group_name} (ID: {group_id}). Response: {response.text}")


def main():
    # Fetch groups from the API
    groups = fetch_groups()
    if not groups:
        print("No groups found. Exiting.")
        return

    print(f"Fetched {len(groups)} groups.")

    # Connect to LDAP
    server = Server(LDAP_SERVER, get_info=ALL)
    conn = Connection(server, LDAP_USER, LDAP_PASSWORD, auto_bind=True)

    for group in groups:
        print(f"Processing group: {group['name']} (LDAP: {group['name']})")

        # Check if the group exists in Active Directory first
        if not check_group_exists(conn, group["name"]):
            print(f"Skipping OpenProject group '{group['name']}' - not found in Active Directory")
            continue

        # Fetch members of the group
        member_dns = fetch_group_members(conn, group["name"])
        member_ids = []

        for member_dn in member_dns:
            user_details = fetch_user_details(conn, member_dn)
            if user_details:
                # Fetch user ID from the API using the email
                user_id = fetch_user_id(user_details["full_name"])
                if user_id:
                    member_ids.append(user_id)

        # Update group members via API
        update_group_members(group["id"], group["name"], member_ids)

    conn.unbind()


if __name__ == "__main__":
    main()
