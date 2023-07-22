import os
import json
from github import Github

# Obtendo o token do Github e o caminho do evento
token = os.getenv('GITHUB_TOKEN')
event_path = os.getenv('GITHUB_EVENT_PATH')

# Inicializando a instância Github
g = Github(token)

# Pegando o repositório atual
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))

# Lendo o arquivo de evento para obter o número do PR
with open(event_path, 'r') as file:
    event = json.load(file)

# Extraindo o número do PR do evento
pull_number = event["pull_request"]["number"]

# Obtendo o PR a partir do número
pr = repo.get_pull(int(pull_number))

# Adicionando um comentário ao PR
pr.create_issue_comment("Obrigado por sua contribuição!")

# Adicionando uma reação ao Issue associado ao PR
issue = repo.get_issue(int(pull_number))
issue.create_reaction("heart")
