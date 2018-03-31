# user customization
# TODO: document other hooks

import os


def chert_post_load(chert_obj):
    _autotag_entries(chert_obj)


def chert_pre_audit(chert_obj):
    # exceptions are automatically caught and logged
    # just enable debug mode to see issues
    raise ValueError('something went awry')


def _autotag_entries(chert_obj):
    # called by post_load
    for entry in chert_obj.entries:
        rel_path = os.path.relpath(entry.source_path, chert_obj.entries_path)
        rel_path, entry_filename = os.path.split(rel_path)
        new_tags = [p.strip() for p in rel_path.split('/') if p.split()]
        for tag in new_tags:
            if tag not in entry.tags:
                entry.tags.append(tag)

    chert_obj._rebuild_tag_map()

    return

###########

from boltons.tableutils import Table
from boltons.timeutils import isoparse

def _entries_to_mdtable(entries):
    headers = ['Project', 'Stars', 'Initial release', 'Releases', 'Current Version']
    rows = []
    for entry in entries:
        initial_release_year = isoparse(entry['first_release_date'].replace('Z', '')).year
        lrel_dt = isoparse(entry['latest_release_date'].replace('Z', ''))
        row = ['[{0}][{0}]'.format(entry['name']),
               '%s' % entry['star_count'],
               '%s (%s)' % (entry['first_release_name'], initial_release_year),
               '%s' % entry['release_count'],
               '%s (%s-%s-%s)' % (entry['latest_release_name'], lrel_dt.year, lrel_dt.month, lrel_dt.day)]
        rows.append(row)

    table = Table.from_data(rows, headers=headers)

    ret = table.to_text()
    ret += '\n\n'
    for entry in entries:
        ret += '\n[%s]: %s' % (entry['name'], entry['url'])

    return ret




if __name__ == '__main__':
    sys.exit(_main() or 0)
