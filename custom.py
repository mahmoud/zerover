"""This module provides custom hooks for the Chert static site generator."""
# user customization
# TODO: document other hooks

import datetime
import json
import sys
from pathlib import Path

from boltons.iterutils import partition
from boltons.tableutils import Table

PROJECT_ROOT_PATH = Path(__file__).parent
PROJECTS_JSON_PATH = PROJECT_ROOT_PATH / "projects.json"

NA_VAL = "---"


def chert_post_load(chert_obj):
    # https://github.com/mahmoud/chert/blob/b4a91b5a66ec5f5002d6e67a2f880709e2e11326/chert/core.py#L840
    with PROJECTS_JSON_PATH.open() as f:
        projects = json.load(f)["projects"]

    zv_projects, emeritus_projects = partition(projects, lambda p: p["is_zerover"])
    zv_project_table = None
    emeritus_project_table = None

    for entry in chert_obj.all_entries:
        for part in entry.loaded_parts:
            content = part["content"]
            if (
                "[ZEROVER_PROJECT_TABLE]" not in content
                and "[EMERITUS_PROJECT_TABLE]" not in content
            ):
                continue
            if zv_project_table is None:
                try:
                    zv_project_table = _zv_to_htmltable(zv_projects)
                except Exception as e:
                    raise e
                emeritus_project_table = _emeritus_to_htmltable(
                    emeritus_projects
                )  # TODO: emeritus table format
            content = content.replace("[ZEROVER_PROJECT_TABLE]", zv_project_table)
            content = content.replace(
                "[EMERITUS_PROJECT_TABLE]", emeritus_project_table
            )
            part["content"] = content


###########


class ZVTable(Table):
    _html_table_tag = '<table class="zv-table">'
    _html_thead = '<thead style="position: sticky; top: 0; background: white;">'

    def get_cell_html(self, data):
        # Table escapes html by default
        return data


def tooltipped(content, tip):
    if not tip:
        return "%s" % content
    return '<span title="%s">%s</span>' % (tip, content)


def _zv_to_htmltable(entries):
    headers = [
        "Project",
        "Stars",
        "First Released",
        "Releases",
        "Current Version",
        "0ver years",
    ]

    def _get_row(entry):
        irel_dt = datetime.datetime.fromisoformat(entry["first_release_date"])
        lrel_dt, zv_streak = None, None
        if entry.get("latest_release_date"):
            lrel_dt = datetime.datetime.fromisoformat(entry["latest_release_date"])
        zv_streak = datetime.datetime.now() - irel_dt.replace(tzinfo=None)
        zv_streak_years = round(zv_streak.days / 365.0, 1)

        row = [
            tooltipped(
                '<a href="%s">%s</a>' % (entry["url"], entry["name"]),
                entry.get("reason"),
            ),
            tooltipped(
                "{:,}".format(entry["star_count"])
                if entry.get("star_count")
                else NA_VAL,
                entry.get("reason"),
            ),
            tooltipped(irel_dt.year, entry.get("first_release_version")),
            "%s" % entry.get("release_count", NA_VAL),
        ]
        if lrel_dt:
            row.append(
                "%s (%s)" % (entry.get("latest_release_version", NA_VAL), lrel_dt.year)
            )
        else:
            row.append(NA_VAL)

        row.append("%s" % zv_streak_years)

        return row

    rows = []
    for entry in entries:
        try:
            row = _get_row(entry)
        except Exception:
            print("failed to load entry: %r" % entry)
            raise
        rows.append(row)

    table = ZVTable.from_data(rows, headers=headers)

    ret = table.to_html()

    # table sorting js at bottom of base.html uses the stars class on
    # the heading to sort properly
    ret = ret.replace("<th>Stars</th>", '<th class="stars">Stars</th>')
    ret = ret.replace("<th>Releases</th>", '<th class="releases">Releases</th>')
    ret += "\n\n"
    return ret


def _emeritus_to_htmltable(entries):
    headers = [
        "Project",
        "Stars",
        "First Released",
        "0ver Releases",
        "Last 0ver release",
        "0ver years",
    ]

    rows = []
    for entry in entries:
        irel_dt = datetime.datetime.fromisoformat(entry["first_release_date"])
        lrel_dt, zv_streak = None, None
        if entry.get("first_nonzv_release_date"):
            lrel_dt = datetime.datetime.fromisoformat(entry["first_nonzv_release_date"])
        zv_streak = lrel_dt.replace(tzinfo=None) - irel_dt.replace(tzinfo=None)
        zv_streak_years = round(zv_streak.days / 365.0, 1)

        row = [
            tooltipped(
                '<a href="%s">%s</a>' % (entry["url"], entry["name"]),
                entry.get("reason"),
            ),
            tooltipped(
                "{:,}".format(entry["star_count"])
                if entry.get("star_count")
                else NA_VAL,
                entry.get("reason"),
            ),
            tooltipped(irel_dt.year, entry.get("first_release_version")),
            "%s" % entry.get("release_count_zv", NA_VAL),
        ]
        if lrel_dt:
            row.append(
                "%s (%s)" % (entry.get("last_zv_release_version", NA_VAL), lrel_dt.year)
            )
        else:
            row.append(NA_VAL)

        row.append("%s" % zv_streak_years)

        rows.append(row)

    table = ZVTable.from_data(rows, headers=headers)

    ret = table.to_html()

    # table sorting js at bottom of base.html uses the stars class on
    # the heading to sort properly
    ret = ret.replace("<th>Stars</th>", '<th class="stars">Stars</th>')
    ret = ret.replace(
        "<th>0ver Releases</th>", '<th class="releases">0ver Releases</th>'
    )
    ret += "\n\n"
    return ret


def main():
    with PROJECTS_JSON_PATH.open() as f:
        projects = json.load(f)["projects"]

    zv_projects, emeritus_projects = partition(projects, lambda p: p["is_zerover"])

    sys.exit(0)


if __name__ == "__main__":
    main()
