import os
import json
import sqlparse
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

# Get the list of files modified in the pull request
files = pull_request.get_files()

# For each file, check if it ends with .sql
for file in files:
    if file.filename.endswith(".sql"):
        # Get the content of the file
        content_file = repo.get_contents(file.filename, ref='refs/pull/{}/head'.format(pull_number))

        # Decode the content of the file
        file_content = content_file.decoded_content.decode('utf-8')

        # Parse the SQL into a list of statements
        parsed = sqlparse.parse(file_content)

        # For each statement
        for statement in parsed:
            # Set a flag for when we're in the GROUP BY clause
            in_group_by = False

            # For each token in the statement
            for token in statement.tokens:
                # If the token is a keyword and is equal to "GROUP BY"
                if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "GROUP BY":
                    in_group_by = True
                elif in_group_by and token.ttype is sqlparse.tokens.Number:
                    raise Exception(f"File {file.filename} uses indices in a GROUP BY statement. Please use column names instead.")
                elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() != "GROUP BY":
                    in_group_by = False
