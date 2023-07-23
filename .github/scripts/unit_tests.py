import os
import json
import re
import sqlparse
from github import Github
from typing import Tuple
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview


def get_pull_request() -> Tuple[PullRequest, PullRequestReview]:
    token = os.getenv('GITHUB_TOKEN')
    event_path = os.getenv('GITHUB_EVENT_PATH')
    g = Github(token)
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    with open(event_path, 'r') as file:
        event = json.load(file)
    pull_number = event["pull_request"]["number"]
    return repo.get_pull(int(pull_number))


def validate_sql_file(pull_request: PullRequest) -> Tuple[bool, str]:
    files = pull_request.get_files()
    for file in files:
        if file.filename.endswith(".sql"):
            content_file = pull_request.head.repo.get_contents(file.filename, ref=pull_request.head.ref)
            file_content = content_file.decoded_content.decode('utf-8')
            parsed = sqlparse.parse(file_content)
            for statement in parsed:
                if not is_valid_statement(str(statement)):
                    return False, f"File {file.filename} uses indices in a GROUP BY statement. Please use column names instead."
    return True, ""


def is_valid_statement(statement: str) -> bool:
    group_by_part = re.search("(?i)GROUP BY(.*)", statement, re.DOTALL)
    if group_by_part:
        items = re.split(",\s*", group_by_part.group(1).strip())
        for item in items:
            if item.isdigit():
                return False
    return True


def review_pr(pull_request: PullRequest, is_valid: bool, message: str) -> None:
    if is_valid:
        pull_request.create_issue_comment("SQL validation successful. Thanks for your contribution!")
    else:
        pull_request.create_issue_comment(message)


def main():
    pull_request = get_pull_request()
    is_valid, message = validate_sql_file(pull_request)

    if is_valid:
        review_pr(pull_request, is_valid, "SQL validation successful. Thanks for your contribution!")
    else:
        review_pr(pull_request, is_valid, message)


if __name__ == "__main__":
    main()
