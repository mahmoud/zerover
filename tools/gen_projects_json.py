import argparse
import os
import re
import sys
import json
import time
import base64
import urllib.request
import datetime
from pprint import pprint

import yaml
from boltons.urlutils import URL
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).parent.parent
VTAG_RE = re.compile(
    r"""
    ^
    [^0-9]*
    (?P<major>\d+)
    \.
    [0-9a-zA-Z_.]+
    """,
    re.VERBOSE,
)

# Tags matching these patterns will be completely skipped
SKIP_PATTERNS = [
    r"^ciflow/",  # pytorch has loads of this noise
    r"^ci/",  # pytorch has loads of this noise
    r"^nightly",  # FreeCol
]

# Version numbers after these patterns should be extracted
STRIP_PATTERNS = [
    r"^mc[0-9.]+-",  # Sodium tags include minecraft version numbers
]


def strip_prefix(tag_name: str) -> str:
    """Strip any non-numeric prefix from the tag name."""
    _, _, tag_name = tag_name.rpartition("/")

    if "-" in tag_name:
        _, _, version = tag_name.partition("-")
        if re.search(r"^\d", version):
            return version

    match = re.search(r"\d", tag_name)
    if match:
        return tag_name[match.start() :]
    return tag_name


def match_vtag(tag_name: str) -> re.Match | None:
    """Match version tags using a more general approach."""
    tag_name = strip_prefix(tag_name)
    return VTAG_RE.match(tag_name)


def version_key(version: str) -> tuple:
    """Extract and convert version numbers to tuple for comparison."""
    clean_version = strip_prefix(version)
    try:
        return tuple(
            int(x) for x in re.split(r"\D+", clean_version) if x and x.isdigit()
        )
    except (TypeError, ValueError):
        return tuple()


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


def _find_dominant_version_pattern(tags: list[dict]) -> list[dict]:
    """Find the most common version tag pattern in a project's tags."""
    patterns = {}
    for tag in tags:
        _, _, tag_name = tag["name"].rpartition("/")

        if any(
            re.search(pattern, tag["name"]) or re.search(pattern, tag_name)
            for pattern in SKIP_PATTERNS
        ):
            continue

        for pattern in STRIP_PATTERNS:
            if re.search(pattern, tag_name):
                prefix, _, version = tag_name.partition("-")
                if re.search(r"^\d", version):
                    tag_name = version
                    break

        match = re.search(r"\d", tag_name)
        if not match:
            continue
        prefix = tag_name[: match.start()]
        if prefix in patterns:
            patterns[prefix].append(tag)
        else:
            patterns[prefix] = [tag]

    if not patterns:
        return []
    return max(patterns.values(), key=len)


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
        tags_data = []

    main_tags = _find_dominant_version_pattern(tags_data)
    vtags_data = [td for td in main_tags if match_vtag(td["name"])]
    if not vtags_data:
        return gh_info

    gh_info["release_count"] = len(vtags_data)

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

    return entries


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate project.json from projects.yaml."
    )

    parser.add_argument(
        "-u",
        "--user",
        type=str,
        default=os.getenv("GH_USER", ""),
        help="GitHub Username for API authentication.",
    )
    parser.add_argument(
        "-k",
        "--token",
        type=str,
        default=os.getenv("GH_TOKEN", ""),
        help="GitHub personal access token for API authentication.",
    )
    parser.add_argument(
        "--disable-caching",
        action="store_true",
        default=os.getenv("ZV_DISABLE_CACHING", "false").lower()
        in [
            "true",
            "1",
            "yes",
        ],
        help="Flag to disable caching.",
    )

    return parser.parse_args()


def main():
    start_time = time.time()

    args = parse_args()

    projects_yaml_path = Path(__file__).parent.parent / "projects.yaml"
    with projects_yaml_path.open() as f:
        projects = yaml.safe_load(f)["projects"]

    if not projects:
        return

    try:
        projects_json_path = Path(__file__).parent.parent / "projects.json"
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

    pprint(entries)

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
