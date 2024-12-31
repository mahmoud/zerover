import argparse
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path
from pprint import pprint
from typing import TypedDict, cast

import requests
import yaml
from boltons.urlutils import URL
from hyperlink import parse
from packaging.version import InvalidVersion, Version


class RegexSubstituionDict(TypedDict):
    remove: str
    """The regex pattern to remove from the tag name."""
    search: str
    """The regex pattern to search for in the tag name to replace with `replace`."""
    replace: str
    """The string to replace the `search` pattern with."""


class GitHubTag:
    def __init__(self, name: str, commit_url: str, committed_date: datetime.datetime):
        self.name = name
        self.processed_name = name
        self.commit_url = commit_url
        self.committed_date = committed_date
        self.version: Version | None = None

    def is_version_compatible(self) -> bool:
        try:
            Version(self.processed_name)
        except InvalidVersion:
            return False
        return True

    def process_name(self, regex_subs: list[RegexSubstituionDict] | None = None):
        for sub in regex_subs or []:
            if sub.get("remove"):
                self.processed_name = re.sub(sub["remove"], "", self.processed_name)
            else:
                self.processed_name = re.sub(
                    sub["search"], sub["replace"], self.processed_name
                )

    def parse_version(self):
        self.version = Version(self.processed_name)


class GitHubAPI:
    def __init__(self, user: str, token: str, org: str, repo: str):
        self.user = user
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.org = org
        self.repo = repo

    def get_repo_info(self) -> dict:
        query = """
        query($owner: String!, $repo: String!) {
            rateLimit {
                remaining
            }
            repository(owner: $owner, name: $repo) {
                stargazerCount
            }
        }
        """
        variables = {"owner": self.org, "repo": self.repo}
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=self.headers,
        )
        data = response.json()

        print(f" (( {data["data"]["rateLimit"]["remaining"]} requests remaining")

        return {"star_count": data["data"]["repository"]["stargazerCount"]}

    def fetch_tags(self) -> list[GitHubTag]:
        query = """
        query($owner: String!, $repo: String!, $cursor: String) {
            rateLimit {
                remaining
            }
            repository(owner: $owner, name: $repo) {
                refs(refPrefix: "refs/tags/", first: 100, after: $cursor, orderBy: {field: TAG_COMMIT_DATE, direction: DESC}) {
                    edges {
                        node {
                            name
                            target {
                                commitUrl
                                ... on Commit {
                                    committedDate
                                }
                                ... on Tag {
                                    target {
                                        ... on Commit {
                                            committedDate
                                        }
                                        ... on Tag {
                                            target {
                                                ... on Commit {
                                                    committedDate
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
        """
        cursor = None
        all_tags = []

        while True:
            variables = {"owner": self.org, "repo": self.repo, "cursor": cursor}
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            data = response.json()

            refs = data["data"]["repository"]["refs"]
            all_tags.extend(refs["edges"])

            if refs["pageInfo"]["hasNextPage"]:
                cursor = refs["pageInfo"]["endCursor"]
            else:
                break

            print(f" (( {data["data"]["rateLimit"]["remaining"]} requests remaining")

        return [
            GitHubTag(
                name=t["node"]["name"],
                commit_url=t["node"]["target"]["commitUrl"],
                committed_date=datetime.datetime.fromisoformat(
                    t["node"]["target"].get("committedDate")
                    or t["node"]["target"]["target"].get("committedDate")
                    or t["node"]["target"]["target"]["target"]["committedDate"]
                ),
            )
            for t in all_tags
        ]


def json_default(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"{obj} is not serializable")


class ProjectsEntry:
    def __init__(
        self,
        name: str,
        url: str | None = None,
        gh_url: str | None = None,
        repo_url: str | None = None,
        wp_url: str | None = None,
        emeritus: bool | None = None,
        reason: str | None = None,
        tag_regex_subs: list[RegexSubstituionDict] | None = None,
        star_count: int | None = None,
        release_count: int | None = None,
        release_count_zv: int | None = None,
        latest_release_date: datetime.datetime | datetime.date | None = None,
        latest_release_version: str | Version | None = None,
        first_release_date: datetime.datetime | datetime.date | None = None,
        first_release_version: str | Version | None = None,
        first_nonzv_release_date: datetime.datetime | datetime.date | None = None,
        first_nonzv_release_version: str | Version | None = None,
        last_zv_release_version: str | Version | None = None,
    ):
        self.name: str = name
        """The name of the project."""
        self.url: str | None = url
        """The project's home page."""
        self.gh_url: str | None = gh_url
        """The project's GitHub repository link."""
        self.repo_url: str | None = repo_url
        """The project's non-GitHub repository link."""
        self.wp_url: str | None = wp_url
        """The project's Wikipedia link."""
        self.emeritus: bool | None = emeritus
        """`true` if the project is no longer ZeroVer"""
        self.is_zerover: bool = bool(self.emeritus)  # TODO: combine with emeritus
        """Whether the project is still ZeroVer."""
        self.reason: str | None = reason
        """The reason this project was added to the 0ver website listing."""
        self.tag_regex_subs: list[RegexSubstituionDict] | None = tag_regex_subs
        """The list of regex substitutions to apply to the tag names before parsing."""
        self.star_count: int | None = star_count
        """The number of stars the project has."""
        self.release_count: int | None = release_count
        """The number of releases the project has had."""
        self.release_count_zv: int | None = release_count_zv
        """The number of releases the project has before it left 0ver."""
        self.latest_release_date: datetime.datetime | datetime.date | None = (
            latest_release_date
        )
        """The date of the latest release."""
        self.latest_release_version: Version | None = (
            Version(latest_release_version)
            if isinstance(latest_release_version, str)
            else latest_release_version
        )
        """The version of the latest release."""
        self.latest_release_tag: str | None = None
        """The tag name of the latest release."""
        self.latest_release_link: str | None = None
        """The URL of the latest release commit."""
        self.first_release_date: datetime.datetime | datetime.date | None = (
            first_release_date
        )
        """The date of the first release."""
        self.first_release_version: Version | None = (
            Version(first_release_version)
            if isinstance(first_release_version, str)
            else first_release_version
        )
        self.first_release_tag: str | None = None
        """The tag name of the first release."""
        self.first_release_link: str | None = None
        """The URL of the first release commit."""
        """The version of the first release."""
        self.first_nonzv_release_date: datetime.datetime | datetime.date | None = (
            first_nonzv_release_date
        )
        """The date of the first non-0ver release."""
        self.first_nonzv_release_version: Version | None = (
            Version(first_nonzv_release_version)
            if isinstance(first_nonzv_release_version, str)
            else first_nonzv_release_version
        )
        """The version of the first non-0ver release."""
        self.first_nonzv_release_tag: str | None = None
        """The tag name of the first non-0ver release."""
        self.first_nonzv_release_link: str | None = None
        """The URL of the first non-0ver release commit."""
        self.last_zv_release_version: Version | None = (
            Version(last_zv_release_version)
            if isinstance(last_zv_release_version, str)
            else last_zv_release_version
        )
        """The last 0ver release before the project left ZeroVer."""

    @classmethod
    def from_dict(cls, info: dict):
        return cls(**info)

    def to_dict(self) -> dict:
        hide = ["tag_regex_subs"]
        return {
            k: v for k, v in self.__dict__.items() if v is not None and k not in hide
        }


class Entry:
    def __init__(self, info: dict, args: argparse.Namespace):
        self.info = ProjectsEntry.from_dict(info)
        if self.info.gh_url:
            self.gh_org = self.info.gh_url.split("/")[3]
            self.gh_repo = self.info.gh_url.split("/")[4]
            self.api = GitHubAPI(args.user, args.token, self.gh_org, self.gh_repo)
        else:
            self.gh_org = None
            self.gh_repo = None
            self.api = None
        self.tags: list[GitHubTag] = []
        self.failed_tags: list[GitHubTag] = []
        self.duplicate_tags: list[GitHubTag] = []

    def update_gh_project_info(self):
        if self.api is None:
            return

        repo_info = self.api.get_repo_info()
        self.info.star_count = repo_info["star_count"]

        self.get_tags()
        # TODO: Do pre releases, release candidates, post release fixes, dev releases, etc. count as releases?
        if not self.tags:
            return

        self.info.release_count = len(self.tags)

        # Latest release
        # TODO: ensure latest_release_version is Version() compatible in the check_projects_json.py script
        if not self.info.latest_release_version:
            latest_release = self.tags[0]
            self.info.latest_release_tag = latest_release.name
            self.info.latest_release_link = latest_release.commit_url
            self.info.latest_release_date = latest_release.committed_date
            self.info.latest_release_version = latest_release.version

        # First release
        first_release = None
        if self.info.first_release_version:
            first_releases = [
                v for v in self.tags if v.version == self.info.first_release_version
            ]
            if first_releases:
                first_release = first_releases[0]
        else:
            first_release = self.tags[-1]
        if first_release:
            self.info.first_release_tag = first_release.name
            self.info.first_release_link = first_release.commit_url
            self.info.first_release_date = first_release.committed_date
            self.info.first_release_version = first_release.version

        # ZeroVer releases
        zv_releases = [t for t in self.tags if t.version and t.version.major == 0]
        self.info.release_count_zv = len(zv_releases)
        print(
            f" .. {self.info.release_count} releases, {self.info.release_count_zv} 0ver"
        )

        self.info.is_zerover = (
            self.info.latest_release_version is not None
            and self.info.latest_release_version.major == 0
        )
        if self.info.is_zerover:
            return

        # Last ZeroVer release
        if not self.info.last_zv_release_version:
            last_zv_release = zv_releases[0]
            self.info.last_zv_release_version = last_zv_release.version

        # First non-ZeroVer release
        if not self.info.first_nonzv_release_version:
            nonzv_releases = [
                t for t in self.tags if t.version and t.version.major != 0
            ]
            first_nonzv_release = nonzv_releases[-1]
            self.info.first_nonzv_release_tag = first_nonzv_release.name
            self.info.first_nonzv_release_link = first_nonzv_release.commit_url
            self.info.first_nonzv_release_date = first_nonzv_release.committed_date
            self.info.first_nonzv_release_version = first_nonzv_release.version

    def get_tags(self):
        if not self.api:
            return

        tags_data = self.api.fetch_tags()

        tag_names = set()
        self.tags = []
        self.failed_tags = []
        self.duplicate_tags = []
        for tag in reversed(tags_data):
            tag.process_name(self.info.tag_regex_subs)
            if tag.processed_name and tag.processed_name in tag_names:
                self.duplicate_tags.append(tag)
                continue
            else:
                tag_names.add(tag.processed_name)

            if tag.is_version_compatible():
                tag.parse_version()
                self.tags.append(tag)
            else:
                self.failed_tags.append(tag)

        self.tags = list(reversed(self.tags))
        self.duplicate_tags = list(reversed(self.duplicate_tags))
        if self.duplicate_tags:
            print(self.info.name, [t.name for t in self.duplicate_tags])
        self.failed_tags = list(reversed(self.failed_tags))


def generate(args: argparse.Namespace):
    start_time = time.time()
    projects_yaml_path = Path(__file__).parent.parent / "projects.yaml"
    with projects_yaml_path.open() as f:
        projects: list[dict] = yaml.safe_load(f)["projects"]

    if not projects:
        return

    projects_json_path = Path(__file__).parent.parent / "projects.json"
    try:
        with projects_json_path.open() as f:
            cur_data = json.load(f)
            cur_projects: list[dict] = cur_data["projects"]
            cur_gen_date = datetime.datetime.fromisoformat(cur_data["gen_date"])
    except (IOError, KeyError):
        cur_projects = []
        cur_gen_date = None

    if cur_gen_date:
        fetch_outdated = (
            datetime.datetime.now() - cur_gen_date.replace(tzinfo=None)
        ) > datetime.timedelta(seconds=3600)
    else:
        fetch_outdated = True

    cur_names = sorted([c["name"] for c in cur_projects])
    new_names = sorted([n["name"] for n in projects])

    if fetch_outdated or cur_names != new_names or args.disable_caching:
        entries: list[dict] = []

        for p in projects:
            print("Processing", p["name"])
            if p.get("skip"):
                continue

            entry = Entry(p, args)
            if not entry.info.url and entry.info.gh_url:
                entry.info.url = entry.info.gh_url

            if entry.info.gh_url:
                entry.update_gh_project_info()

            entries.append(entry.info.to_dict())

        entries = sorted(entries, key=lambda e: e["name"])
    else:
        print("Current data already up to date, exiting.")
        return

    pprint(entries)

    res = {
        "projects": entries,
        "gen_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gen_duration": time.time() - start_time,
    }

    with projects_json_path.open("w") as f:
        json.dump(res, f, indent=2, sort_keys=True, default=json_default)


def info(args: argparse.Namespace):
    print("Processing", args.name_or_link)

    if parse(args.name_or_link).scheme in ("http", "https"):
        info = {"gh_url": args.name_or_link}
    else:
        info = get_entry_from_name(args.name_or_link)

    entry = Entry(info, args)
    entry.update_gh_project_info()

    print()
    pprint(entry.info.to_dict())


def tags(args: argparse.Namespace):
    print("Processing", args.name_or_link)

    if parse(args.name_or_link).scheme in ("http", "https"):
        info = {"gh_url": args.name_or_link}
    else:
        info = get_entry_from_name(args.name_or_link)

    entry = Entry(info, args)
    entry.get_tags()

    print("\nParsed tags:")
    for t in entry.tags:
        print(f"{t.name} (parsed as {t.version})")
    if not entry.tags:
        print("No tags parsed.")
    if entry.duplicate_tags:
        print("\nDuplicate tags:")
        for t in entry.duplicate_tags:
            print(f"{t.name} (parsed as {t.processed_name})")
    if entry.failed_tags:
        print("\nFailed tags:")
        for t in entry.failed_tags:
            print(f"{t.name} (tried {t.processed_name})")


def parse_args():
    def add_options(parser: argparse.ArgumentParser, *, caching: bool = False):
        parser.add_argument(
            "-u",
            "--user",
            type=str,
            default=os.getenv("GH_USER", ""),
            help='GitHub Username for API authentication. Falls back to the "GH_USER" environment variable.',
        )
        parser.add_argument(
            "-k",
            "--token",
            type=str,
            default=os.getenv("GH_TOKEN", ""),
            help='A path to a file containing a GitHub personal access token for API authentication. Falls back to the "GH_TOKEN" environment variable.',
        )
        if caching:
            parser.add_argument(
                "--disable-caching",
                action="store_true",
                default=os.getenv("ZV_DISABLE_CACHING", "false").lower()
                in [
                    "true",
                    "1",
                    "yes",
                ],
                help='Flag to disable caching. Falls back to the "ZV_DISABLE_CACHING" environment variable.',
            )

    parser = argparse.ArgumentParser(
        description="Generate or update project.json using projects.yaml."
    )
    add_options(parser, caching=True)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate
    generate_parser = subparsers.add_parser(
        "generate", help="Generate an updated projects.json file."
    )
    add_options(generate_parser, caching=True)

    # Info
    info_parser = subparsers.add_parser(
        "info",
        help="Print automatically pulled info for a GitHub project for debugging.",
    )
    info_parser.add_argument(
        "name_or_link",
        type=str,
        help="The project.yaml exact entry name or GitHub link.",
    )
    add_options(info_parser)

    # Tags
    tags_parser = subparsers.add_parser(
        "tags", help="Print all sorted tags for a GitHub project for debugging."
    )
    tags_parser.add_argument(
        "name_or_link",
        type=str,
        help="The project.yaml exact entry name or GitHub link.",
    )
    add_options(tags_parser)

    args = parser.parse_args()

    if args.command is None:
        args.command = "generate"

    if Path(args.token).is_file():
        with Path(args.token).open() as f:
            args.token = f.read().strip()

    return args


def get_entry_from_name(name: str) -> dict:
    projects_yaml_path = Path(__file__).parent.parent / "projects.yaml"
    with projects_yaml_path.open() as f:
        projects = yaml.safe_load(f)["projects"]
    matching_info = [p for p in projects if p["name"] == name]
    if not matching_info:
        print("No matching project found.")
        sys.exit(1)
    return matching_info[0]


def main():
    args = parse_args()
    if args.command == "generate":
        generate(args)
    elif args.command == "info":
        info(args)
    elif args.command == "tags":
        tags(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if os.getenv("CI"):
            raise e
        print(f" !! debugging unexpected {e}")

        import pdb

        pdb.post_mortem()
        raise e
