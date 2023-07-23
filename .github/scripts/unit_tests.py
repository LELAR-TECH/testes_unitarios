import os
import json
import sqlparse
from github import Github
from typing import Tuple
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview


def get_pull_request() -> Tuple[PullRequest, PullRequestReview]:
    # Get the Github token and PR number from environment variables
    token = os.getenv('GITHUB_TOKEN')
    event_path = os.getenv('GITHUB_EVENT_PATH')

    # Create a Github instance using the token
    g = Github(token)

    # Get the repository
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))

    # Read the event file to get the pull request number
    with open(event_path, 'r') as file:
        event = json.load(file)
    pull_number = event["pull_request"]["number"]

    # Get the pull request
    return repo.get_pull(int(pull_number))


def validate_sql_file(pull_request: PullRequest) -> Tuple[bool, str]:
    # Get the list of files modified in the pull request
    files = pull_request.get_files()

    # For each file, check if it ends with .sql
    for file in files:
        if file.filename.endswith(".sql"):
            # Get and decode the content of the file
            content_file = pull_request.head.repo.get_contents(file.filename, ref=pull_request.head.ref)
            file_content = content_file.decoded_content.decode('utf-8')

            # Parse the SQL into a list of statements
            parsed = sqlparse.parse(file_content)

            # For each statement
            for statement in parsed:
                # Validate the statement
                if not is_valid_statement(statement):
                    return False, f"File {file.filename} uses indices in a GROUP BY statement. Please use column names instead."
    return True, ""


def is_valid_statement(statement) -> bool:
    # Set a flag for when we're in the GROUP BY clause
    in_group_by = False

    # For each token in the statement
    for token in statement.tokens:
        # If the token is a keyword and is equal to "GROUP BY"
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "GROUP BY":
            in_group_by = True
        elif in_group_by and token.ttype is sqlparse.tokens.Number:
            return False
        elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() != "GROUP BY":
            in_group_by = False

    return True


def review_pr(pull_request: PullRequest, is_valid: bool, message: str):
    # Create review
    review = pull_request.create_review(body=message, commit=pull_request.head.sha)

    # Set review state
    if is_valid:
        review.set_review_state(state="APPROVE")
    else:
        review.set_review_state(state="REQUEST_CHANGES")


def main():
    pull_request = get_pull_request()
    is_valid, message = validate_sql_file(pull_request)

    if is_valid:
        review_pr(pull_request, is_valid, "SQL validation successful. Thanks for your contribution!")
    else:
        review_pr(pull_request, is_valid, message)


if __name__ == "__main__":
    main()