import os
import json
import re
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


def validate_sql_file(pull_request: PullRequest) -> Tuple[bool, list]:
    # Get the list of files modified in the pull request
    files = pull_request.get_files()

    error_comments = []

    # For each file, check if it ends with .sql
    for file in files:
        if file.filename.endswith(".sql"):
            # Get and decode the content of the file
            content_file = pull_request.head.repo.get_contents(file.filename, ref=pull_request.head.ref)
            file_content = content_file.decoded_content.decode('utf-8')

            # Parse the SQL into a list of statements
            parsed = sqlparse.parse(file_content)

            # For each statement
            for i, statement in enumerate(parsed, start=1):
                # Validate the statement
                if not is_valid_statement(str(statement)):
                    error_comments.append((file.filename, i, "This line uses indices in a GROUP BY statement. Please use column names instead."))
    return len(error_comments) == 0, error_comments


def is_valid_statement(statement: str) -> bool:
    # Encontra a parte GROUP BY na query
    group_by_part = re.search("(?i)GROUP BY(.*)", statement, re.DOTALL)

    if group_by_part:
        # Remove espaços em branco e divide as palavras
        items = re.split(",\s*", group_by_part.group(1).strip())

        # Verifica se todos os items são palavras (não números)
        for item in items:
            if item.isdigit():
                return False
    return True


def review_pr(pull_request: PullRequest, is_valid: bool, comments: list) -> None:
    if is_valid:
        commit = pull_request.base.repo.get_commit(pull_request.head.sha)
        pull_request.create_review(event="APPROVE", body="SQL validation successful. Thanks for your contribution!", commit=commit)
    else:
        review_comments = [pull_request.create_review_comment(comment[2], pull_request.head.sha, comment[0], comment[1]) for comment in comments]
        pull_request.create_review(event="REQUEST_CHANGES", body="Some lines use indices in a GROUP BY statement. Please use column names instead.", comments=review_comments, commit=pull_request.head.sha)


def main():
    pull_request = get_pull_request()
    is_valid, comments = validate_sql_file(pull_request)

    if is_valid:
        review_pr(pull_request, is_valid, [])
    else:
        review_pr(pull_request, is_valid, comments)


if __name__ == "__main__":
    main()
