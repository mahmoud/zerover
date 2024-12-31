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

import yaml
from boltons.urlutils import URL
from hyperlink import parse
from packaging.version import InvalidVersion, Version


def if_version_compatible(version: str) -> bool:
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


def _get_gh_rel_data(rel_info: dict, args: argparse.Namespace) -> dict:
    ret = {}
    ret["tag"] = rel_info["name"]
    ret["version"] = None
    if match_vtag(ret["tag"]):
        ret["version"] = strip_prefix(ret["tag"])
    ret["api_commit_url"] = rel_info["commit"]["url"]
    rel_data = _get_gh_json(ret["api_commit_url"], args)
    if isinstance(rel_data, dict):
        ret["date"] = rel_data["commit"]["author"]["date"]
        ret["link"] = rel_data["html_url"]
    return ret


def parse_tags(
    tags_data: list[dict], regex_subs: list[dict] | None = None
) -> tuple[list[dict], list[dict], list[dict]]:
    tag_names = set()
    parsed_tags_data = []
    failed_tags_data = []
    duplicate_tags_data = []

    for tag in reversed(tags_data):
        tag_name = tag["name"]
        if regex_subs:
            for sub in regex_subs:
                if sub.get("remove"):
                    tag_name = re.sub(sub["remove"], "", tag_name)
                else:
                    tag_name = re.sub(sub["replace"], sub["with"], tag_name)
        if tag_name in tag_names:
            tag["sub_name"] = tag_name
            duplicate_tags_data.append(tag)
            continue
        else:
            tag_names.add(tag_name)

        if if_version_compatible(tag_name):
            tag["py_version"] = Version(tag_name)
            parsed_tags_data.append(tag)
        else:
            tag["sub_name"] = tag_name
            failed_tags_data.append(tag)

    return (
        list(reversed(parsed_tags_data)),
        list(reversed(failed_tags_data)),
        duplicate_tags_data,
    )


def get_gh_project_info(info: dict, args: argparse.Namespace) -> dict:
    gh_info = {}
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
    tags_data = _get_gh_json(gh_url.to_text(), args)
    if isinstance(tags_data, dict):
        return gh_info

    parsed_tags_data, _, _ = parse_tags(tags_data, info.get("tag_regex_subs"))
    if not parsed_tags_data:
        return gh_info

    gh_info["release_count"] = len(set(parsed_tags_data))

    latest_release = vtags_data[0]
    latest_release_data = _get_gh_rel_data(latest_release, args)
    for k, v in latest_release_data.items():
        gh_info[f"latest_release_{k}"] = v

    vtags_data.sort(key=lambda x: version_key(x["name"]), reverse=True)

    first_release_version = info.get("first_release_version")
    first_release = None
    if first_release_version is None:
        first_release = [
            v
            for v in vtags_data
            if version_key(v["name"]) < version_key(latest_release["name"])
        ][-1]
    else:
        first_releases = [v for v in vtags_data if v["name"] == first_release_version]
        if first_releases:
            first_release = first_releases[0]
    if first_release:
        first_release_data = _get_gh_rel_data(first_release, args)
        for k, v in first_release_data.items():
            gh_info[f"first_release_{k}"] = v

    zv_releases = []
    for rel in vtags_data:
        match = match_vtag(rel["name"])
        if match and match.group("major") == "0":
            zv_releases.append(rel)
    gh_info["release_count_zv"] = len(zv_releases)
    print(
        f' .. {gh_info["release_count"]} releases, {gh_info["release_count_zv"]} 0ver'
    )

    is_zerover = latest_release in zv_releases

    gh_info["is_zerover"] = is_zerover

    if is_zerover:
        return gh_info

    last_zv_release = zv_releases[0]
    first_nonzv_release = vtags_data[vtags_data.index(last_zv_release) - 1]
    first_nonzv_release_data = _get_gh_rel_data(first_nonzv_release, args)

    gh_info["last_zv_release_version"] = last_zv_release["name"]
    for k, v in first_nonzv_release_data.items():
        gh_info[f"first_nonzv_release_{k}"] = v

    return gh_info


def json_default(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"{obj} is not serializable")


def fetch_entries(projects: list[dict], args: argparse.Namespace) -> list[dict]:
    entries = []

    for p in projects:
        print("Processing", p["name"])
        info = dict(p)
        if info.get("skip"):
            continue

        info["url"] = info.get("url", info.get("gh_url"))

        if info.get("gh_url"):
            gh_info = get_gh_project_info(info, args)
            # Only add new data, preserve any manual information
            info.update({k: v for k, v in gh_info.items() if k not in info})

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


def main():
    args = parse_args()
    if args.command == "generate":
        generate(args)
    elif args.command == "info":
        print("Processing", args.name_or_link)
        gh_info = get_gh_project_info({"gh_url": args.name_or_link}, args)
        print()
        pprint(gh_info)
    elif args.command == "tags":
        print("Processing", args.name_or_link)

        if parse(args.name_or_link).scheme in ("http", "https"):
            info = {"gh_url": args.name_or_link}
        else:
            projects_yaml_path = Path(__file__).parent.parent / "projects.yaml"
            with projects_yaml_path.open() as f:
                projects = yaml.safe_load(f)["projects"]
            matching_info = [p for p in projects if p["name"] == args.name_or_link]
            if not matching_info:
                print("No matching project found.")
                return
            info = matching_info[0]

        org, repo = URL(info["gh_url"].rstrip("/")).path_parts[1:]
        gh_url = URL("https://api.github.com/repos")
        gh_url.path_parts += (org, repo, "tags")

        tags_data = _get_gh_json(gh_url.to_text(), args)
        if isinstance(tags_data, dict):
            tags_data = []

        parsed_tags_data, failed_tags_data, duplicate_tag_names = parse_tags(
            tags_data, info.get("tag_regex_subs")
        )

        print("\nParsed tags:")
        for t in parsed_tags_data:
            print(f"{t['name']} (parsed as {t['py_version']})")
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
            cur_projects = cur_data["projects"]
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
