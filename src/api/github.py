import requests

from src.api.models import GitHubRepo


class GitHubAPI:

    def __init__(self, token=None):
        self.base_url = "https://api.github.com/"
        self.headers = {}
        if token:
            raise NotImplementedError('Token not necessary at current capacity - TBA')

    def _pull_raw_repo_metadata(self, owner, repo):
        endpoint = f"repos/{owner}/{repo}"
        full_url = self.base_url + endpoint
        res = requests.get(full_url, headers=self.headers)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def _validate_raw_data(raw_data):
        return GitHubRepo(**raw_data)

    def get_repo_metadata(self, owner, repo):
        raw_data = self._pull_raw_repo_metadata(owner, repo)
        return self._validate_raw_data(raw_data)
