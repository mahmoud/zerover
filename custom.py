# user customization
# TODO: document other hooks

import os

CUR_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECTS_JSON_PATH = os.path.join(CUR_PATH, 'projects.json')

NA_VAL = '---'


def chert_post_load(chert_obj):
    with open(PROJECTS_JSON_PATH) as f:
        data = json.load(f)
        projects = data['projects']

    zv_projects, emeritus_projects = partition(projects, lambda p: p['is_zerover'])
    zv_project_table = None
    emeritus_project_table = None

    for entry in chert_obj.all_entries:
        for part in entry.loaded_parts:
            content = part['content']
            if '[ZEROVER_PROJECT_TABLE]' not in content and '[EMERITUS_PROJECT_TABLE]' not in content:
                continue
            if zv_project_table is None:
                zv_project_table = _zv_to_htmltable(zv_projects)
                emeritus_project_table = _emeritus_to_htmltable(emeritus_projects)  # TODO: emeritus table format
            content = content.replace('[ZEROVER_PROJECT_TABLE]', zv_project_table)
            content = content.replace('[EMERITUS_PROJECT_TABLE]', emeritus_project_table)
            part['content'] = content
    return


###########

import sys
import json
import datetime

from boltons.iterutils import partition
from boltons.tableutils import Table
from boltons.timeutils import isoparse

class ZVTable(Table):
    _html_table_tag = '<table class="zv-table">'

    def get_cell_html(self, data):
        # Table escapes html by default
        return data


def tooltipped(content, tip):
    if not tip:
        return '%s' % content
    return '<span title="%s">%s</span>' % (tip, content)


def _zv_to_htmltable(entries):
    headers = ['Project', 'Stars', 'First Released', 'Releases', 'Current Version', '0ver years']

    rows = []
    for entry in entries:
        irel_dt = isoparse(entry['first_release_date'].replace('Z', ''))  # TODO: boltons Z handling
        lrel_dt, zv_streak = None, None
        if entry.get('latest_release_date'):
            lrel_dt = isoparse(entry['latest_release_date'].replace('Z', ''))
        zv_streak = datetime.datetime.utcnow() - irel_dt
        zv_streak_years = round(zv_streak.days / 365.0, 1)

        row = [tooltipped('<a href="%s">%s</a>' % (entry['url'], entry['name']),
                          entry.get('reason')),
               tooltipped('{:,}'.format(entry['star_count']) if entry.get('star_count') else NA_VAL,
                          entry.get('reason')),
               tooltipped(irel_dt.year, entry.get('first_release_version')),
               '%s' % entry.get('release_count', NA_VAL)]
        if lrel_dt:
            row.append('%s (%s)' % (entry.get('latest_release_version', NA_VAL), lrel_dt.year))
        else:
            row.append(NA_VAL)

        row.append('%s' % zv_streak_years)

        rows.append(row)

    table = ZVTable.from_data(rows, headers=headers)

    ret = table.to_html()

    # table sorting js at bottom of base.html uses the stars class on
    # the heading to sort properly
    ret = ret.replace('<th>Stars</th>', '<th class="stars">Stars</th>')
    ret = ret.replace('<th>Releases</th>', '<th class="releases">Releases</th>')
    ret += '\n\n'
    return ret


def _emeritus_to_htmltable(entries):
    headers = ['Project', 'Stars', 'First Released', '0ver Releases', 'Last 0ver release', '0ver years']

    rows = []
    for entry in entries:
        irel_dt = isoparse(entry['first_release_date'].replace('Z', ''))  # TODO: boltons Z handling
        lrel_dt, zv_streak = None, None
        if entry.get('first_nonzv_release_date'):
            lrel_dt = isoparse(entry['first_nonzv_release_date'].replace('Z', ''))
        zv_streak = lrel_dt - irel_dt
        zv_streak_years = round(zv_streak.days / 365.0, 1)

        row = [tooltipped('<a href="%s">%s</a>' % (entry['url'], entry['name']),
                          entry.get('reason')),
               tooltipped('{:,}'.format(entry['star_count']) if entry.get('star_count') else NA_VAL,
                          entry.get('reason')),
               tooltipped(irel_dt.year, entry.get('first_release_version')),
               '%s' % entry.get('release_count_zv', NA_VAL)]
        if lrel_dt:
            row.append('%s (%s)' % (entry.get('last_zv_release_version', NA_VAL), lrel_dt.year))
        else:
            row.append(NA_VAL)

        row.append('%s' % zv_streak_years)

        rows.append(row)

    table = ZVTable.from_data(rows, headers=headers)

    ret = table.to_html()

    # table sorting js at bottom of base.html uses the stars class on
    # the heading to sort properly
    ret = ret.replace('<th>Stars</th>', '<th class="stars">Stars</th>')
    ret = ret.replace('<th>0ver Releases</th>', '<th class="releases">0ver Releases</th>')
    ret += '\n\n'
    return ret


def _main():
    with open('projects.json') as f:
        data = json.load(f)
        projects = data['projects']

    zv_projects, emeritus_projects = partition(projects, lambda p: p['is_zerover'])

    return


if __name__ == '__main__':
    sys.exit(_main() or 0)
