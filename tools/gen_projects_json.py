import argparse
import base64
import datetime
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from pprint import pprint
from typing import TypedDict, cast

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


class ProjectsInputEntryDict(TypedDict):
    name: str
    """The name of the project."""
    url: str
    """The project's home page."""
    gh_url: str
    """The project's GitHub repository link."""
    repo_url: str
    """The project's non-GitHub repository link."""
    wp_url: str
    """The project's Wikipedia link."""
    emeritus: bool
    """`true` if the project is no longer ZeroVer"""
    reason: str
    """The reason this project was added to the 0ver website listing."""
    tag_regex_subs: list[RegexSubstituionDict]
    """The list of regex substitutions to apply to the tag names before parsing."""
    star_count: int
    """The number of stars the project has."""
    release_count: int
    """The number of releases the project has had."""
    release_count_zv: int
    """The number of releases the project has before it left 0ver."""
    latest_release_date: datetime.datetime | datetime.date
    """The date of the latest release."""
    latest_release_version: str | Version
    """The version of the latest release."""
    first_release_date: datetime.datetime | datetime.date
    """The date of the first release."""
    first_release_version: str | Version
    """The version of the first release."""
    first_nonzv_release_date: datetime.datetime | datetime.date
    """The date of the first non-0ver release."""
    first_nonzv_release_version: str | Version
    """The version of the first non-0ver release."""
    last_zv_release_version: str | Version
    """The last 0ver release before the project left ZeroVer."""


class ProjectsOutputEntryDict(ProjectsInputEntryDict):
    is_zerover: bool
    """Whether the project is still ZeroVer."""


class GitHubTagCommitDict(TypedDict):
    sha: str
    url: str


class GitHubTagDict(TypedDict):
    name: str
    """The name of the tag."""
    zipball_url: str
    tarball_url: str
    commit: GitHubTagCommitDict
    node_id: str


class GitHubParsedTagDict(GitHubTagDict):
    version: Version
    """The parsed PEP 440 compatible version object."""


class GitHubDebugTagDict(GitHubTagDict):
    sub_name: str
    """The tag name after applying regex substitutions."""


class GitHubDetailedTagDict(TypedDict):
    tag: str
    """The name of the tag."""
    version: Version
    """The parsed PEP 440 compatible version object."""
    api_commit_url: str
    """The API URL of the commit."""
    date: datetime.datetime
    """The date of the commit."""
    link: str
    """The URL of the commit."""


class GitHubInfoDict(TypedDict):
    star_count: int
    """The number of stars the project has."""
    release_count: int
    """The number of releases the project has had."""
    release_count_zv: int
    """The number of releases the project has before it left 0ver."""
    latest_release_date: datetime.datetime | datetime.date
    """The date of the latest release."""
    latest_release_version: str | Version
    """The version of the latest release."""
    first_release_date: datetime.datetime | datetime.date
    """The date of the first release."""
    first_release_version: str | Version
    """The version of the first release."""
    first_nonzv_release_date: datetime.datetime | datetime.date
    """The date of the first non-0ver release."""
    first_nonzv_release_version: str | Version
    """The version of the first non-0ver release."""
    last_zv_release_version: str | Version
    """The last 0ver release before the project left ZeroVer."""
    is_zerover: bool
    """Whether the project is still ZeroVer."""


def json_default(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"{obj} is not serializable")


def is_version_compatible(version: str) -> bool:
    try:
        Version(version)
    except InvalidVersion:
        return False
    return True


def _get_gh_json(url: str, args: argparse.Namespace) -> dict | list[dict]:
    """
    Get paginated results from GitHub, possibly authorized based on command
    line arguments or environment variables.
    """
    req = urllib.request.Request(url)
    if args.user and args.token:
        auth_str = f"{args.user}:{args.token}"
        auth_bytes = auth_str.encode("ascii")
        auth_header_val = f'Basic {base64.b64encode(auth_bytes).decode("ascii")}'
        req.add_header("Authorization", auth_header_val)

    resp = urllib.request.urlopen(req)
    body = resp.read()
    res = json.loads(body)
    rate_rem = int(resp.info().get("x-ratelimit-remaining", "-1"))

    if not isinstance(res, list) or not res:
        print(f" (( {rate_rem} requests remaining")
        return res

    page = 2
    ret = res
    while res:
        paged_url = f"{url}?page={page}"
        req = urllib.request.Request(paged_url)
        if args.user and args.token:
            req.add_header("Authorization", auth_header_val)
        resp = urllib.request.urlopen(req)
        body = resp.read()
        res = json.loads(body)
        ret.extend(res)
        page += 1

    rate_rem = int(resp.info().get("x-ratelimit-remaining", "-1"))
    print(f" (( {rate_rem} requests remaining")
    return ret


def _get_gh_rel_data(
    rel_info: GitHubParsedTagDict, args: argparse.Namespace
) -> GitHubDetailedTagDict:
    rel_data: dict = _get_gh_json(rel_info["commit"]["url"], args)  # type: ignore
    return {
        "tag": rel_info["name"],
        "version": rel_info["version"],
        "api_commit_url": rel_info["commit"]["url"],
        "date": rel_data["commit"]["author"]["date"],
        "link": rel_data["html_url"],
    }


def parse_tags(
    tags_data: list[GitHubTagDict], regex_subs: list[RegexSubstituionDict] | None = None
) -> tuple[
    list[GitHubParsedTagDict], list[GitHubDebugTagDict], list[GitHubDebugTagDict]
]:
    """Parse the list of GitHub tags returning the tags with the PEP 440 compatible version objects.

    Parameters
    ----------
    tags_data: list[dict]
        The list of GitHub tags to parse from the API.
    regex_subs: list[RegexSubstituionDict] | None = None
        The list of regex substitutions from projects.yaml to apply to the tag names before parsing.

    Returns:
    parsed_tags_data: list[dict]
        The list of properly parsed tags with the added "version" key.
    failed_tags_data: list[dict]
        The list of tags that failed to be parsed with the added "sub_name" key for debugging.
    duplicate_tags_data: list[dict]
        The list of duplicate tags with the added "sub_name" key for debugging.
    """
    tag_names: set[str] = set()
    parsed_tags_data: list[GitHubParsedTagDict] = []
    failed_tags_data: list[GitHubDebugTagDict] = []
    duplicate_tags_data: list[GitHubDebugTagDict] = []

    for tag in reversed(tags_data):
        tag_name = tag["name"]
        if regex_subs:
            for sub in regex_subs:
                if sub.get("remove"):
                    tag_name = re.sub(sub["remove"], "", tag_name)
                else:
                    tag_name = re.sub(sub["search"], sub["replace"], tag_name)
        if tag_name in tag_names:
            duplicate_tags_data.append({**tag, "sub_name": tag_name})
            continue
        else:
            tag_names.add(tag_name)

        if is_version_compatible(tag_name):
            parsed_tags_data.append({**tag, "version": Version(tag_name)})
        else:
            failed_tags_data.append({**tag, "sub_name": tag_name})

    return (
        list(reversed(parsed_tags_data)),
        list(reversed(failed_tags_data)),
        duplicate_tags_data,
    )


def get_gh_project_info(
    info: ProjectsInputEntryDict, args: argparse.Namespace
) -> GitHubInfoDict:
    gh_info: GitHubInfoDict = {}  # type: ignore
    url = info.get("gh_url")
    if url is None:
        return gh_info

    org, repo = URL(url.rstrip("/")).path_parts[1:]
    gh_url = URL("https://api.github.com/repos")
    gh_url.path_parts += (org, repo)

    project_data = _get_gh_json(gh_url.to_text(), args)
    if isinstance(project_data, dict):
        gh_info["star_count"] = project_data["stargazers_count"]

    gh_url.path_parts += ("tags",)
    tags_data: list[GitHubTagDict] = _get_gh_json(gh_url.to_text(), args)  # type: ignore
    parsed_tags_data, _, _ = parse_tags(tags_data, info.get("tag_regex_subs"))
    if not parsed_tags_data:
        return gh_info

    gh_info["release_count"] = len(parsed_tags_data)

    # Latest release
    if "latest_release_date" not in info or "latest_release_version" not in info:
        latest_release = parsed_tags_data[0]
        latest_release_data = _get_gh_rel_data(latest_release, args)
        for k, v in latest_release_data.items():
            gh_info[f"latest_release_{k}"] = v
    else:
        info["latest_release_version"] = Version(info["latest_release_version"])  # type: ignore
        # TODO: ensure latest_release_version is Version() compatible in the check_projects_json.py script

    # Sort after grabbing the latest release
    # TODO: check if this is needed
    # parsed_tags_data.sort(key=lambda x: x["version"], reverse=True)

    # First release
    first_release = None
    if "first_release_version" in info:
        first_releases = [
            v for v in parsed_tags_data if v["name"] == info["first_release_version"]
        ]
        if first_releases:
            first_release = first_releases[0]
    else:
        first_release = parsed_tags_data[-1]
    if first_release:
        first_release_data = _get_gh_rel_data(first_release, args)
        for k, v in first_release_data.items():
            gh_info[f"first_release_{k}"] = v

    # ZeroVer releases
    zv_releases = []
    for rel in parsed_tags_data:
        if rel["version"].major == 0:
            zv_releases.append(rel)
    gh_info["release_count_zv"] = len(zv_releases)
    print(
        f' .. {gh_info["release_count"]} releases, {gh_info["release_count_zv"]} 0ver'
    )

    gh_info["is_zerover"] = gh_info["latest_release_version"].major == 0  # type: ignore
    if gh_info["is_zerover"]:
        return gh_info

    # Last ZeroVer release
    last_zv_release = zv_releases[0]
    gh_info["last_zv_release_version"] = last_zv_release["name"]

    # First non-ZeroVer release
    first_nonzv_release = parsed_tags_data[parsed_tags_data.index(last_zv_release) - 1]
    first_nonzv_release_data = _get_gh_rel_data(first_nonzv_release, args)
    for k, v in first_nonzv_release_data.items():
        gh_info[f"first_nonzv_release_{k}"] = v

    return gh_info


def fetch_entries(
    projects: list[ProjectsInputEntryDict], args: argparse.Namespace
) -> list[ProjectsOutputEntryDict]:
    entries: list[ProjectsOutputEntryDict] = []

    for p in projects:
        print("Processing", p["name"])
        info: ProjectsOutputEntryDict = cast(ProjectsOutputEntryDict, p)
        if info.get("skip"):
            continue

        info["url"] = info.get("url", info.get("gh_url"))

        if info.get("gh_url"):
            gh_info = get_gh_project_info(p, args)
            # Only add new data, preserve any manual information
            info.update({k: v for k, v in gh_info.items() if k not in info})  # type: ignore

        info["is_zerover"] = info.get("is_zerover", not info.get("emeritus", False))

        entries.append(info)

    return sorted(entries, key=lambda e: e["name"])


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


def get_entry_from_name(name: str) -> ProjectsInputEntryDict:
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
        print("Processing", args.name_or_link)

        if parse(args.name_or_link).scheme in ("http", "https"):
            info = {"gh_url": args.name_or_link}
        else:
            info = get_entry_from_name(args.name_or_link)

        gh_info = get_gh_project_info(info, args)  # type: ignore

        print()
        pprint(gh_info)
    elif args.command == "tags":
        print("Processing", args.name_or_link)

        if parse(args.name_or_link).scheme in ("http", "https"):
            info = {"gh_url": args.name_or_link}
        else:
            info = get_entry_from_name(args.name_or_link)

        org, repo = URL(info["gh_url"].rstrip("/")).path_parts[1:]
        gh_url = URL("https://api.github.com/repos")
        gh_url.path_parts += (org, repo, "tags")

        tags_data: list[GitHubTagDict] = _get_gh_json(gh_url.to_text(), args)  # type: ignore
        parsed_tags_data, failed_tags_data, duplicate_tag_names = parse_tags(
            tags_data, info.get("tag_regex_subs")
        )

        print("\nParsed tags:")
        for t in parsed_tags_data:
            print(f"{t['name']} (parsed as {t['version']})")
        if not parsed_tags_data:
            print("No tags parsed.")
        if duplicate_tag_names:
            print("\nDuplicate tags:")
            for t in duplicate_tag_names:
                print(f"{t['name']} (parsed as {t['sub_name']})")
        if failed_tags_data:
            print("\nFailed tags:")
            for t in failed_tags_data:
                print(f"{t['name']} (tried {t['sub_name']})")


def generate(args: argparse.Namespace):
    start_time = time.time()
    projects_yaml_path = Path(__file__).parent.parent / "projects.yaml"
    with projects_yaml_path.open() as f:
        projects = yaml.safe_load(f)["projects"]

    if not projects:
        return

    projects_json_path = Path(__file__).parent.parent / "projects.json"
    try:
        with projects_json_path.open() as f:
            cur_data = json.load(f)
            cur_projects: list[ProjectsInputEntryDict] = cur_data["projects"]
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
        entries = fetch_entries(projects, args)
    else:
        print("Current data already up to date, exiting.")
        return

    # pprint(entries)

    res = {
        "projects": entries,
        "gen_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gen_duration": time.time() - start_time,
    }

    with projects_json_path.open("w") as f:
        json.dump(res, f, indent=2, sort_keys=True, default=json_default)

    sys.exit(0)


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
