import os
import json
import re
import sqlparse
from github import Github
from typing import Tuple
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview


def get_pull_request() -> Tuple[PullRequest, PullRequestReview]:
    github_token = os.getenv('GITHUB_TOKEN')
    event_path = os.getenv('GITHUB_EVENT_PATH')
    github_api = Github(github_token)
    repository = github_api.get_repo(os.getenv('GITHUB_REPOSITORY'))

    with open(event_path, 'r') as file:
        event = json.load(file)

    pull_number = event["pull_request"]["number"]
    return repository.get_pull(int(pull_number))


def validate_sql_file(pull_request: PullRequest) -> Tuple[bool, str]:
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
    group_by_clause = re.search("(?i)GROUP BY(.*)", statement, re.DOTALL)

    if group_by_clause:
        items = re.split(",\s*", group_by_clause.group(1).strip())

        for item in items:
            if item.isdigit():
                return False

    return True


def main():
    pull_request = get_pull_request()
    validation_status, validation_message = validate_sql_file(pull_request)

    if validation_status:
        with open("output.txt", "w") as f:
            f.write("SQL validation successful. Thanks for your contribution!")
    else:
        with open("output.txt", "w") as f:
            f.write(validation_message)


if __name__ == "__main__":
    main()
