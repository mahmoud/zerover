# user customization
# TODO: document other hooks

import os

CUR_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECTS_JSON_PATH = os.path.join(CUR_PATH, 'projects.json')


def chert_post_load(chert_obj):
    with open(PROJECTS_JSON_PATH) as f:
        data = json.load(f)
        projects = data['projects']

    zv_projects, alumni_projects = partition(projects, lambda p: p['is_zerover'])
    zv_project_table = None
    alumni_project_table = None

    for entry in chert_obj.all_entries:
        for part in entry.loaded_parts:
            content = part['content']
            if '[ZEROVER_PROJECT_TABLE]' not in content and '[ALUMNI_PROJECT_TABLE]' not in content:
                continue
            if zv_project_table is None:
                zv_project_table = _entries_to_mdtable(zv_projects)
                alumni_project_table = _entries_to_mdtable(alumni_projects)
            content = content.replace('[ZEROVER_PROJECT_TABLE]', zv_project_table)
            content = content.replace('[ALUMNI_PROJECT_TABLE]', alumni_project_table)
            part['content'] = content
    return


###########

import sys
import json

from boltons.iterutils import partition
from boltons.tableutils import Table
from boltons.timeutils import isoparse

def _entries_to_mdtable(entries):
    headers = ['Project', 'Stars', 'Initial release', 'Releases', 'Current Version']
    rows = []
    for entry in entries:
        initial_release_year = isoparse(entry['first_release_date'].replace('Z', '')).year
        lrel_dt = None
        if entry.get('latest_release_date'):
            lrel_dt = isoparse(entry['latest_release_date'].replace('Z', ''))

        row = ['[{0}][{0}]'.format(entry['name']),
               '%s' % entry.get('star_count', '-'),
               '%s (%s)' % (entry.get('first_release_name', '0.0.1'), initial_release_year),
               '%s' % entry.get('release_count', '-')]
        if lrel_dt:
            row.append('%s (%s-%s-%s)' % (entry.get('latest_release_name', '-'), lrel_dt.year, lrel_dt.month, lrel_dt.day))
        else:
            row.append('-')
        rows.append(row)

    table = Table.from_data(rows, headers=headers)

    ret = table.to_text()
    ret += '\n\n'
    for entry in entries:
        ret += '\n[%s]: %s' % (entry['name'], entry.get('url', '-'))

    ret = ret.replace('-+-', '-|-')  # TODO: hack until boltons table fixes

    return ret


def _main():
    with open('projects.json') as f:
        data = json.load(f)
        projects = data['projects']

    zv_projects, alumni_projects = partition(projects, lambda p: p['is_zerover'])

    print _entries_to_mdtable(zv_projects)
    print
    print _entries_to_mdtable(alumni_projects)


if __name__ == '__main__':
    sys.exit(_main() or 0)
