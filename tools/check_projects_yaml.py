import datetime
import sys
import yaml
from schema import Schema, Or, Optional
from hyperlink import parse
from pathlib import Path


def check_url(url_str: str):
    url = parse(url_str)
    assert url.scheme in ("http", "https")
    return True


OPTIONAL = {
    Optional("gh_url"): check_url,
    Optional("reason"): str,
    Optional("repo_url"): str,
    Optional("wp_url"): str,
    Optional("emeritus"): bool,
    Optional("release_count"): int,
    Optional("release_count_zv"): int,
    Optional("star_count"): int,
    Optional("first_nonzv_release_api_commit_url"): str,
    Optional("first_nonzv_release_date"): Or(datetime.date, datetime.datetime),
    Optional("first_nonzv_release_link"): str,
    Optional("first_nonzv_release_tag"): str,
    Optional("first_nonzv_release_version"): Or(float, str),
    Optional("first_release_api_commit_url"): str,
    Optional("first_release_date"): Or(datetime.date, datetime.datetime),
    Optional("first_release_link"): str,
    Optional("first_release_tag"): str,
    Optional("first_release_version"): Or(float, str),
    Optional("last_zv_release_version"): Or(float, str),
    Optional("latest_release_api_commit_url"): str,
    Optional("latest_release_date"): Or(datetime.date, datetime.datetime),
    Optional("latest_release_link"): str,
    Optional("latest_release_tag"): str,
    Optional("latest_release_version"): Or(float, str),
}
IN_SCHEMA = Schema(
    {
        "projects": [
            Or(
                # GitHub projects
                {
                    **OPTIONAL,
                    "name": str,
                    "gh_url": check_url,
                    Optional("url"): check_url,  # Overrides gh_url for the hyperlink
                },  # type: ignore
                # Non-GitHub projects
                {
                    **OPTIONAL,
                    "name": str,
                    "url": check_url,
                    "first_release_date": Or(datetime.date, datetime.datetime),
                },  # type: ignore
            )
        ],
    },
)


def redundant(src: list[str]):
    """Returns a list of redundant items in the source list."""
    items = []
    duplicates = set()

    for item in src:
        if item in items:
            duplicates.add(item)
        else:
            items.append(item)

    return duplicates


def main():
    projects_yaml_path = Path(__file__).parent.parent / "projects.yaml"
    with projects_yaml_path.open() as f:
        data = yaml.safe_load(f)

    IN_SCHEMA.validate(data)

    projects = data["projects"]

    dup_names = redundant([p["name"].lower() for p in projects])
    if dup_names:
        print(f"Found {len(dup_names)} project(s) with duplicate names: {dup_names}")
        sys.exit(1)

    dup_urls = redundant([p.get("gh_url", p.get("url")) for p in projects])
    if dup_urls:
        print(f"Found {len(dup_urls)} project(s) with duplicate urls: {dup_urls}")
        sys.exit(1)

    print("projects.yaml validated successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
