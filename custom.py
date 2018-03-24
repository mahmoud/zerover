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

import re
import sys
import json
import urllib2

import yaml
from boltons.urlutils import URL
from boltons.tableutils import Table

vtag_re = re.compile(r'^v?(?P<major>\d+)\.[0-9.]+$')

def _get_gh_json(url):
    resp = json.loads(urllib2.urlopen(url).read())
    if not isinstance(resp, list) or not resp:
        return resp
    page = 2
    ret = resp
    while resp:
        paged_url = url + '?page=%s' % page
        resp = json.loads(urllib2.urlopen(paged_url).read())
        ret.extend(resp)
        page += 1
    return ret


def _get_gh_rel_data(rel_info):
    ret = {}
    ret['name'] = rel_info['name']
    ret['api_commit_url'] = rel_info['commit']['url']
    rel_data = _get_gh_json(ret['api_commit_url'])
    ret['date'] = rel_data['commit']['author']['date']
    ret['link'] = rel_data['html_url']
    return ret


def _main():
    with open('projects.yaml') as f:
        zv_projects = yaml.load(f)

    zv_entries = []
    hm_entries = []

    for p in zv_projects:
        print 'processing', p['name']
        if not p.get('gh_url'):
            continue
        org, repo = URL(p['gh_url']).path_parts[1:]
        gh_url = URL('https://api.github.com/repos')
        gh_url.path_parts += (org, repo)

        project_url = gh_url.to_text()
        project_data = _get_gh_json(project_url)
        star_count = project_data['stargazers_count']

        gh_url.path_parts += ('tags',)
        tags_url = gh_url.to_text()
        tags_data = _get_gh_json(tags_url)
        vtags_data = [td for td in tags_data if vtag_re.match(td['name'])]
        release_count = len(vtags_data)

        first_release = vtags_data[-1]
        first_release_data = _get_gh_rel_data(first_release)

        latest_release = vtags_data[0]
        latest_release_data = _get_gh_rel_data(latest_release)

        zv_releases = [rel for rel in vtags_data
                            if vtag_re.match(rel['name']).group('major') == '0']
        is_zerover = zv_releases[0] == latest_release

        info = dict(p)
        info['star_count'] = star_count
        info['release_count'] = release_count
        info['first_release'] = first_release_data
        info['latest_release'] = latest_release_data
        info['is_zerover'] = is_zerover

        if is_zerover:
            zv_entries.append(info)
            continue

        last_zv_release = zv_releases[0]
        last_zv_release_data = _get_gh_rel_data(last_zv_release)

        info['last_zv_release'] = last_zv_release_data

        hm_entries.append(info)

    from pprint import pprint
    pprint(zv_entries)
    pprint(hm_entries)


    return


if __name__ == '__main__':
    sys.exit(_main() or 0)
