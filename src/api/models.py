import re
from datetime import datetime, date, timezone
from pydantic import BaseModel, model_validator, field_validator, Field
from typing import Optional


GITHUB_URL_PATTERN = re.compile(
    r'(https?://(?:www\.)?github\.com/([a-zA-Z0-9-]+)/([\w.-]+))(?:/.*)?/?'
)


class PyPIPackageReleaseMD(BaseModel):
    """Single release's metadata"""
    version: str
    release_dt: datetime = Field(alias='upload_time_iso_8601')
    source_size: int


class PyPIPackage(BaseModel):
    """Top level package metadata"""
    name: str
    version: str
    summary: str | None = None
    # dependencies: list[str] = Field(default_factory=list)
    releases: list[PyPIPackageReleaseMD] = Field(default_factory=list)
    github_url: str | None = None
    github_owner: str | None = None
    github_repo_name: str | None = None
    github_repo_name_full: str | None = None
    snapshot_dt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('releases', mode='before')
    @classmethod
    def extract_release_metadata(cls, releases):

        if not isinstance(releases, dict):
            return []

        processed_releases = []
        for version, files in releases.items():
            sdist_size = None
            release_dt = None

            for file_info in files:
                if file_info.get('packagetype') == 'sdist':
                    sdist_size = file_info.get('size')
                if release_dt is None and file_info.get('upload_time_iso_8601'):
                    release_dt = file_info.get('upload_time_iso_8601')

            if sdist_size is not None and release_dt is not None:
                processed_releases.append({
                    'version': version,
                    'upload_time_iso_8601': release_dt,
                    'source_size': sdist_size
                })
        return processed_releases

    @model_validator(mode='before')
    @classmethod
    def process_info_and_urls(cls, data):

        if not isinstance(data, dict):
            return data

        info_data = data.get('info', {})

        # Get name, version, and summary
        data['name'] = info_data.get('name')
        data['version'] = info_data.get('version')
        data['summary'] = info_data.get('summary')

        # Handle dependencies
        if info_data.get('requires_dist'):
            data['dependencies'] = info_data.get('requires_dist', [])

        # Get github URL
        project_urls = info_data.get('project_urls', {})
        for url_name, url in project_urls.items():
            match = GITHUB_URL_PATTERN.search(url)
            if match:
                data['github_url'] = match.group(1)
                data['github_owner'] = match.group(2)
                data['github_repo_name'] = match.group(3)
                data['github_repo_name_full'] = f'{match.group(2)}/{match.group(3)}'
                break  # is found

        # If no github URL found, try home_page
        if not 'github_url' in data and 'home_page' in info_data:
            match = GITHUB_URL_PATTERN.search(info_data.get('home_page'))
            if match:
                data['github_url'] = match.group(1)
                data['github_owner'] = match.group(2)
                data['github_repo_name'] = match.group(3)
                data['github_repo_name_full'] = f'{match.group(2)}/{match.group(3)}'

        return data


class PyPIPackageDownloadCount(BaseModel):
    """Per row download query"""
    package_name: str = Field(alias='project')
    dt: date = Field(alias='timestamp')
    download_count: int
    version: str | None = None
    country_code: str | None = None


class GitHubRepo(BaseModel):
    repo_name: str = Field(alias='name')
    repo_name_full: str = Field(alias='full_name')
    repo_url: str = Field(alias='html_url')
    description: str | None = None
    forks_count: int
    stargazers_count: int
    subscribers_count: int
    open_issues_count: int
    # topics: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    snapshot_dt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
