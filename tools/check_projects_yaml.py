import sys
import yaml
from schema import Schema, Or
from hyperlink import parse
from pathlib import Path


def check_url(url_str):
    url = parse(url_str)
    assert url.scheme in ("http", "https")
    return url


IN_SCHEMA = Schema(
    {
        "projects": [
            {
                "name": str,
                Or("url", "gh_url", "repo_url"): check_url,
            },
        ],
    },
    ignore_extra_keys=True,
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
