import json
import os


CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "repositories.json"
)


def load_repositories():
    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    return data["repositories"]


def get_repository(name):
    repositories = load_repositories()

    for repository in repositories:
        if repository["name"] == name:
            return repository

    return None