import datetime
import sys
from pathlib import Path

import yaml
from boltons.iterutils import redundant
from hyperlink import parse
from schema import Optional, Or, Schema


def check_url(url_str: str):
    url = parse(url_str)
    assert url.scheme in ("http", "https")
    return True


OPTIONAL = {
    Optional("gh_url"): check_url,
    Optional("repo_url"): str,
    Optional("wp_url"): str,
    Optional("emeritus"): bool,
    Optional("reason"): str,
    Optional("star_count"): int,
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
                    Optional("emeritus"): False,
                    Optional("url"): check_url,  # Overrides gh_url for the hyperlink
                    Optional("release_count"): int,
                    Optional("latest_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("latest_release_version"): Or(float, str),
                    Optional("first_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("first_release_version"): Or(float, str),
                },  # type: ignore
                # Emeritus GitHub projects
                {
                    **OPTIONAL,
                    "name": str,
                    "gh_url": check_url,
                    "emeritus": True,
                    Optional("url"): check_url,  # Overrides gh_url for the hyperlink
                    Optional("release_count_zv"): int,
                    Optional("first_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("first_release_version"): Or(float, str),
                    Optional("first_nonzv_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("first_nonzv_release_version"): Or(float, str),
                    Optional("last_zv_release_version"): Or(float, str),
                },  # type: ignore
                # Non-GitHub projects
                {
                    **OPTIONAL,
                    "name": str,
                    "url": check_url,
                    Optional("emeritus"): False,
                    Optional("release_count"): int,
                    "first_release_date": Or(datetime.date, datetime.datetime),
                    Optional("latest_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("latest_release_version"): Or(float, str),
                    Optional("first_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("first_release_version"): Or(float, str),
                },  # type: ignore
                # Emeritus Non-GitHub projects
                {
                    **OPTIONAL,
                    "name": str,
                    "url": check_url,
                    "emeritus": True,
                    Optional("release_count_zv"): int,
                    "first_release_date": Or(datetime.date, datetime.datetime),
                    Optional("first_release_version"): Or(float, str),
                    Optional("first_nonzv_release_date"): Or(
                        datetime.date, datetime.datetime
                    ),
                    Optional("first_nonzv_release_version"): Or(float, str),
                    Optional("last_zv_release_version"): Or(float, str),
                },  # type: ignore
            )
        ],
    },
)


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
