import os
import re
from github import Github

# Get the Github token and PR number from environment variables
token = os.getenv('GITHUB_TOKEN')
pr_number = os.getenv('GITHUB_EVENT_PATH')

# Create a Github instance using the token
g = Github(token)

# Get the pull request
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))

# Read the event file to get the pull request number
with open(pr_number, 'r') as file:
    event = json.load(file)
pull_number = event["number"]

pull_request = repo.get_pull(int(pull_number))

# Regex to match GROUP BY statements with indices instead of column names
group_by_index_pattern = re.compile(r"GROUP\s+BY\s+[0-9]+", re.IGNORECASE)

# Get the list of files modified in the pull request
files = pull_request.get_files()

# For each file, check if it ends with .sql and if it does, check for GROUP BY indices
for file in files:
    if file.filename.endswith(".sql"):
        if group_by_index_pattern.search(file.patch):
            raise Exception(f"File {file.filename} uses indices in a GROUP BY statement. Please use column names instead.")
