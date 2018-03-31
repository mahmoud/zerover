
# TODO: build a json file out of the following, have the custom.py
# just turn that json into a table.
# add note about getting a token from here: https://github.com/settings/tokens

import os
import re
import sys
import json
import base64
import urllib2
import datetime

import yaml
from boltons.urlutils import URL
from boltons.fileutils import atomic_save

vtag_re = re.compile(r'^v?(?P<major>\d+)\.[0-9.]+')

def _get_gh_json(url):
    gh_user = os.getenv('GH_USER', '')
    gh_token = os.getenv('GH_TOKEN', '')
    req = urllib2.Request(url)
    if gh_user and gh_token:
        auth_header_val = 'Basic %s' % base64.b64encode('%s:%s' % (gh_user, gh_token))
        req.add_header('Authorization', auth_header_val)
    resp = urllib2.urlopen(req)
    body = resp.read()
    res = json.loads(body)
    rate_rem = int(resp.info().dict.get('x-ratelimit-remaining', '-1'))

    if not isinstance(res, list) or not res:
        print ' (( %s requests remaining' % rate_rem
        return res
    page = 2
    ret = res
    while res:
        paged_url = url + '?page=%s' % page
        req = urllib2.Request(paged_url)
        if gh_user and gh_token:
            req.add_header('Authorization', auth_header_val)
        resp = urllib2.urlopen(req)
        body = resp.read()
        res = json.loads(body)
        ret.extend(res)
        page += 1
    rate_rem = int(resp.info().dict.get('x-ratelimit-remaining', '-1'))
    print ' (( %s requests remaining' % rate_rem
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
        zv_projects = yaml.load(f)['projects']

    zv_entries = []
    hm_entries = []

    for p in zv_projects:
        print 'processing', p['name']
        info = dict(p)
        if not p.get('gh_url'):
            continue
        if p.get('skip'):
            continue
        p['url'] = p.get('url', p['gh_url'])
        org, repo = URL(p['gh_url']).path_parts[1:]
        gh_url = URL('https://api.github.com/repos')
        gh_url.path_parts += (org, repo)

        project_url = gh_url.to_text()
        project_data = _get_gh_json(project_url)
        info['star_count'] = project_data['stargazers_count']

        gh_url.path_parts += ('tags',)
        tags_url = gh_url.to_text()
        tags_data = _get_gh_json(tags_url)
        vtags_data = [td for td in tags_data if vtag_re.match(td['name'])]
        info['release_count'] = len(vtags_data)
        print ' .. %s releases' % info['release_count']

        first_release = vtags_data[-1]
        first_release_data = _get_gh_rel_data(first_release)
        for k, v in first_release_data.items():
            info['first_release_%s' % k] = v

        latest_release = vtags_data[0]
        latest_release_data = _get_gh_rel_data(latest_release)
        for k, v in latest_release_data.items():
            info['latest_release_%s' % k] = v

        zv_releases = [rel for rel in vtags_data
                            if vtag_re.match(rel['name']).group('major') == '0']
        is_zerover = zv_releases[0] == latest_release

        info['is_zerover'] = is_zerover

        if is_zerover:
            zv_entries.append(info)
            continue

        last_zv_release = zv_releases[0]
        last_zv_release_data = _get_gh_rel_data(last_zv_release)

        for k, v in last_zv_release_data.items():
            info['last_zv_release_%s' % k] = v

        hm_entries.append(info)

    from pprint import pprint

    pprint(zv_entries)
    pprint(hm_entries)

    res = {'zv_entries': zv_entries,
           'hm_entries': hm_entries,
           'gen_date': datetime.datetime.utcnow().isoformat()}
    with atomic_save('entries.json') as f:
        f.write(json.dumps(res, indent=2, sort_keys=True))

    import pdb;pdb.set_trace()

    return


if __name__ == '__main__':
    sys.exit(_main() or 0)
