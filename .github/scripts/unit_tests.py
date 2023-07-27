import os
import json
import re
import sqlparse
from github import Github
from typing import Tuple
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview


def get_pull_request() -> Tuple[PullRequest, PullRequestReview]:
    """
    Get pull request using GitHub API

    Returns:
        PullRequest object
    """
    github_token = os.getenv('GITHUB_TOKEN')
    event_path = os.getenv('GITHUB_EVENT_PATH')
    github_api = Github(github_token)
    repository = github_api.get_repo(os.getenv('GITHUB_REPOSITORY'))

    with open(event_path, 'r') as file:
        event = json.load(file)

    pull_number = event["pull_request"]["number"]
    return repository.get_pull(int(pull_number))


def validate_sql_file(pull_request: PullRequest) -> Tuple[bool, str]:
    """
    Validate sql file in the pull request.
    
    Args:
        pull_request: A pull request object
    
    Returns:
        A tuple where the first element is a boolean indicating whether the SQL file is valid
        and the second element is a message string.
    """
    changed_files = pull_request.get_files()

    for file in changed_files:
        if file.filename.endswith(".sql"):
            content_file = pull_request.head.repo.get_contents(file.filename, ref=pull_request.head.ref)
            file_content = content_file.decoded_content.decode('utf-8')
            parsed_sql = sqlparse.parse(file_content)

            for statement in parsed_sql:
                if not is_valid_sql_statement(str(statement)):
                    return False, f"File {file.filename} uses indices in a GROUP BY statement. Please use column names instead."

    return True, ""


def is_valid_sql_statement(statement: str) -> bool:
    """
    Check if a SQL statement is valid.
    
    Args:
        statement: A SQL statement as a string
    
    Returns:
        A boolean indicating whether the SQL statement is valid.
    """
    group_by_clause = re.search("(?i)GROUP BY(.*)", statement, re.DOTALL)

    if group_by_clause:
        items = re.split(",\s*", group_by_clause.group(1).strip())

        for item in items:
            if item.isdigit():
                return False

    return True


def review_pr(pull_request: PullRequest, is_valid: bool, message: str) -> None:
    """
    Add a review comment to the pull request.

    Args:
        pull_request: A pull request object
        is_valid: A boolean indicating whether the SQL file is valid
        message: A message string to include in the review comment
    """
    if is_valid:
        review_message = "SQL validation successful. Thanks for your contribution!"
    else:
        review_message = message

    # Set the review message as an environment variable
    os.environ["REVIEW_MESSAGE"] = review_message

    # Create the review
    if is_valid:
        pull_request.create_review(event="APPROVE", body=review_message)
    else:
        pull_request.create_review(event="REQUEST_CHANGES", body=review_message)


def main():
    """
    Main function to get pull request, validate SQL file and review pull request.
    """
    pull_request = get_pull_request()
    validation_status, validation_message = validate_sql_file(pull_request)

    if validation_status:
        review_pr(pull_request, validation_status, "SQL validation successful. Thanks for your contribution!")
    else:
        review_pr(pull_request, validation_status, validation_message)


if __name__ == "__main__":
    main()
