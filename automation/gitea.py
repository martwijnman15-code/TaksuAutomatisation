
import os
from pathlib import Path

from dotenv import load_dotenv

from git import Repo
from github import Github, Auth

load_dotenv()

class GitHubService:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.github = None
        self.user = None
        self.repo = None

    # GITHUB AUTHENTICATION

    def login(self, token=None):
        self.token = token or self.token

        if not self.token:
            raise ValueError("GitHub token is required")

        client = Github(auth=Auth.Token(self.token))

        try:
            user = client.get_user()
            username = user.login

            self.github = client
            self.user = user

            return {
                "username": username,
                "name": user.name,
                "avatar": user.avatar_url
            }
        except Exception:
            client.close()
            raise

    def require_login(self):
        if self.github is None or self.user is None:
            raise RuntimeError("Please login first")

    # GITHUB PROJECTS

    def get_projects(self):
        self.require_login()

        return [
            {
                "name": repository.name,
                "full_name": repository.full_name,
                "url": repository.html_url,
                "private": repository.private
            }
            for repository in self.user.get_repos()
        ]

    def create_project(
        self,
        name,
        description="",
        private=True
    ):
        self.require_login()

        repository = self.user.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=True
        )

        return {
            "name": repository.name,
            "url": repository.html_url
        }

    def delete_project(self, full_name):
        self.require_login()

        repository = self.github.get_repo(full_name)
        repository.delete()

        return True

    def get_branches(self, full_name):
        self.require_login()

        repository = self.github.get_repo(full_name)

        return [
            branch.name
            for branch in repository.get_branches()
        ]

    # LOCAL GIT OPERATIONS

    def open_project(self, path):
        self.repo = Repo(path)
        return self.repo.working_tree_dir

    def clone_project(self, url, path):
        if Path(path).exists():
            raise FileExistsError(
                "Destination already exists"
            )

        self.repo = Repo.clone_from(url, path)
        return self.repo.working_tree_dir

    def require_repo(self):
        if self.repo is None:
            raise RuntimeError("No Git project selected")

    def commit(self, message):
        self.require_repo()

        self.repo.git.add(A=True)

        if not self.repo.is_dirty(index=True):
            return False

        self.repo.index.commit(message)
        return True

    def uncommit(self):
        self.require_repo()

        self.repo.git.reset("--mixed", "HEAD~1")

    def push(self, branch):
        self.require_repo()

        return self.repo.git.push("origin", branch)

    def pull(self, branch):
        self.require_repo()

        return self.repo.git.pull("origin", branch)

    def fetch(self):
        self.require_repo()

        for remote in self.repo.remotes:
            remote.fetch()

    def change_branch(self, branch):
        self.require_repo()

        self.repo.git.checkout(branch)

        return self.repo.active_branch.name

    def make_branch(self, name):
        self.require_repo()

        new_branch = self.repo.create_head(name)
        new_branch.checkout()

        return new_branch.name

    def logout(self):
        if self.github:
            self.github.close()

        self.github = None
        self.user = None
        self.token = None
