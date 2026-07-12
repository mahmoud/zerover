import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import gen_projects_json

import unittest
import tempfile
from unittest import mock

GH_URL = "https://github.com/example/proj"


def _tag(name: str) -> dict:
    """Tag entry as returned by the GitHub /tags API (distinct commit URL per tag)."""
    return {
        "name": name,
        "commit": {
            "url": f"https://api.github.com/repos/example/proj/commits/{name}"
        },
    }


def _fake_gh_json(tag_names: list[str], dates: dict[str, str]):
    """Fake for _get_gh_json dispatching on URL: repo info, tag list, or commit."""
    tags = [_tag(name) for name in tag_names]

    def fake(url, user=None, token=None):
        if url.endswith("/tags"):
            return tags
        _, sep, tag_name = url.rpartition("/commits/")
        if sep:
            return {
                "commit": {"author": {"date": dates[tag_name]}},
                "html_url": f"https://github.com/example/proj/tree/{tag_name}",
            }
        if url.startswith("https://api.github.com/repos/"):
            return {"stargazers_count": 4321}
        raise AssertionError(f"unexpected GitHub API URL: {url!r}")

    return fake


def _patched_project_info(info: dict, tag_names: list[str], dates: dict[str, str]) -> dict:
    with mock.patch.object(
        gen_projects_json, "_get_gh_json", _fake_gh_json(tag_names, dates)
    ):
        return gen_projects_json.get_gh_project_info(info)


class TestFindDominantVersionPattern(unittest.TestCase):
    """Contract: v/V-prefixed and bare tags form one group; CI noise is
    skipped; other prefixes stay in their own (here losing) groups."""

    RUFF_STYLE = ["v0.4.10", "v0.4.9", "0.5.0", "0.12.4"]

    def _dominant_names(self, tag_names):
        tags = [_tag(name) for name in tag_names]
        result = gen_projects_json._find_dominant_version_pattern(tags)
        return {tag["name"] for tag in result}

    def test_merges_v_prefixed_and_bare_tags(self):
        self.assertEqual(
            self._dominant_names(self.RUFF_STYLE), set(self.RUFF_STYLE)
        )

    def test_skip_patterns_exclude_ci_noise(self):
        self.assertEqual(
            self._dominant_names(self.RUFF_STYLE + ["ciflow/1.2.3"]),
            set(self.RUFF_STYLE),
        )

    def test_distinct_prefix_stays_in_losing_group(self):
        self.assertEqual(
            self._dominant_names(self.RUFF_STYLE + ["druid-0.1.0"]),
            set(self.RUFF_STYLE),
        )


class TestGetGhProjectInfo(unittest.TestCase):
    def test_latest_release_is_version_sorted_not_api_order(self):
        # API order deliberately name-sorted (as GitHub /tags returns), newest last.
        tag_names = ["v0.4.10", "v0.4.9", "0.5.0", "0.12.4"]
        dates = {
            "v0.4.10": "2024-06-20T00:00:00Z",
            "v0.4.9": "2024-06-14T00:00:00Z",
            "0.5.0": "2024-07-01T00:00:00Z",
            "0.12.4": "2025-07-10T00:00:00Z",
        }
        gh_info = _patched_project_info(
            {"name": "Ruffish", "gh_url": GH_URL}, tag_names, dates
        )
        self.assertEqual(gh_info["latest_release_version"], "0.12.4")
        self.assertEqual(gh_info["latest_release_date"], dates["0.12.4"])
        # min-by-version, not last-in-API-order
        self.assertEqual(gh_info["first_release_version"], "0.4.9")
        self.assertEqual(gh_info["release_count"], 4)
        self.assertTrue(gh_info["is_zerover"])

    def test_single_matching_tag(self):
        dates = {"v0.1.0": "2020-05-05T00:00:00Z"}
        gh_info = _patched_project_info(
            {"name": "Solo", "gh_url": GH_URL}, ["v0.1.0"], dates
        )
        self.assertEqual(gh_info["latest_release_version"], "0.1.0")
        self.assertEqual(
            gh_info["first_release_version"], gh_info["latest_release_version"]
        )
        self.assertEqual(gh_info["first_release_date"], dates["v0.1.0"])

    def test_manual_first_release_version_matches_prefixed_tag(self):
        dates = {
            "v1.0.0": "2023-01-01T00:00:00Z",
            "v0.3.0": "2019-03-03T00:00:00Z",
        }
        gh_info = _patched_project_info(
            {"name": "Reactish", "gh_url": GH_URL, "first_release_version": "0.3.0"},
            ["v1.0.0", "v0.3.0"],
            dates,
        )
        self.assertEqual(gh_info["first_release_version"], "0.3.0")
        self.assertEqual(gh_info["first_release_tag"], "v0.3.0")
        self.assertEqual(gh_info["first_release_date"], dates["v0.3.0"])

    def test_emeritus_project_reports_zv_boundary(self):
        dates = {
            "v1.0.0": "2023-01-01T00:00:00Z",
            "v0.9.0": "2022-09-09T00:00:00Z",
        }
        gh_info = _patched_project_info(
            {"name": "Emeritus", "gh_url": GH_URL}, ["v1.0.0", "v0.9.0"], dates
        )
        self.assertFalse(gh_info["is_zerover"])
        self.assertEqual(gh_info["last_zv_release_version"], "v0.9.0")
        self.assertEqual(gh_info["first_nonzv_release_version"], "1.0.0")
        self.assertEqual(gh_info["first_nonzv_release_date"], dates["v1.0.0"])


class TestVersionKey(unittest.TestCase):
    def test_numeric_ordering_across_prefix_styles(self):
        self.assertGreater(
            gen_projects_json.version_key("v0.4.10"),
            gen_projects_json.version_key("v0.4.9"),
        )
        self.assertGreater(
            gen_projects_json.version_key("0.12.4"),
            gen_projects_json.version_key("v0.4.10"),
        )


class TestParseArgsToken(unittest.TestCase):
    """Contract: after parsing, -k/--token is replaced by file contents only
    when it names a readable file; literal tokens pass through unchanged,
    including tokens long enough that the file probe raises OSError."""

    def _parse(self, token_arg: str):
        with mock.patch.object(sys, "argv", ["prog", "-k", token_arg]):
            return gen_projects_json.parse_args()

    def test_long_literal_token_survives_raising_stat(self):
        # On Linux/Python 3.13 Path.is_file() raises OSError(ENAMETOOLONG)
        # for values longer than NAME_MAX (the real Actions GITHUB_TOKEN did);
        # macOS silently returns False, so simulate the raise.
        token = "g" * 300
        with mock.patch.object(
            gen_projects_json.Path,
            "is_file",
            side_effect=OSError(36, "File name too long"),
        ):
            args = self._parse(token)
        self.assertEqual(args.token, token)

    def test_token_file_path_replaced_by_stripped_contents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.txt"
            token_file.write_text("sekrit\n")
            args = self._parse(str(token_file))
        self.assertEqual(args.token, "sekrit")

    def test_short_literal_token_passes_through(self):
        args = self._parse("notafile_gtk123")
        self.assertEqual(args.token, "notafile_gtk123")


if __name__ == "__main__":
    unittest.main()
