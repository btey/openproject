# custom_scripts/get_version.py
import os
import re
import subprocess
import gitlab

def get_version():
    # Read the version.rb file
    with open('./lib/open_project/version.rb', 'r') as file:
        content = file.read()

    # Extract version information using regex
    major = re.search(r'MAJOR\s*=\s*(\d+)', content).group(1)
    minor = re.search(r'MINOR\s*=\s*(\d+)', content).group(1)
    patch = re.search(r'PATCH\s*=\s*(\d+)', content).group(1)

    version = f"{major}.{minor}.{patch}"

    # Get the current branch name from the environment variable
    branch = os.getenv('CI_COMMIT_REF_NAME')

    # Get all tags that match the version format
    tags = subprocess.check_output(["git", "tag", "--list", f"{version}*"]).strip().decode('utf-8')

    # Count the number of tags based on the branch name
    count = len(re.findall(rf"{version}-\d+", tags))
    new_version = f"{version}-{count + 1}"

    print(f"Current branch: {branch}")
    print(f"Version: {new_version}")

    # Check if the tag already exists
    existing_tags = subprocess.check_output(["git", "tag"]).strip().decode('utf-8').split('\n')
    if new_version in existing_tags:
        print(f"Tag {new_version} already exists.")
    else:
        # Create a new tag
        subprocess.check_call(["git", "tag", new_version])

        # # Push the new tag to the remote repository using the GitLab API
        api_token = os.getenv('GITLAB_API_TOKEN')
        gl = gitlab.Gitlab('https://git.bethelservice.org', private_token=api_token)
        project = gl.projects.get('cdsupportdevelopers/general/openproject')
        project.tags.create({'tag_name': new_version, 'ref': branch})

    # Store the new version in an environment variable
    os.environ['APP_VERSION'] = new_version

    # Write the new version to a file
    with open('version.env', 'w') as f:
        f.write(f"APP_VERSION={new_version}\n")

if __name__ == "__main__":
    get_version()
