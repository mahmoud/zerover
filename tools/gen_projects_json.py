# for now, run like:
#   GH_USER=user GH_TOKEN=$(cat /path/to/token/file) python tools/gen_entry_json.py
# get a token from here: https://github.com/settings/tokens

import os
import re
import sys
import json
import time
import base64
import urllib2
import datetime

import yaml
from boltons.urlutils import URL
from boltons.fileutils import atomic_save

PREFIXES = ['v',   # common
            'rel-',  # theano
            'orc-']  # orc

VTAG_RE = re.compile(r'^(?P<major>\d+)\.[0-9.]+')

def match_zv_tag(tag_name, prefixes):
    # TODO: could combine these all into the re
    for prefix in prefixes:
        if tag_name.startswith(prefix):
            tag_name = tag_name[len(prefix):]
            break
    return VTAG_RE.match(tag_name)


def _get_gh_json(url):
    """"
    Get paginated results from GitHub, possibly authorized based on
    GH_USER/GH_TOKEN env vars.
    """
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


def get_gh_project_info(url):
    ret = {}

    org, repo = URL(url).path_parts[1:]
    gh_url = URL('https://api.github.com/repos')
    gh_url.path_parts += (org, repo)

    project_url = gh_url.to_text()
    project_data = _get_gh_json(project_url)
    ret['star_count'] = project_data['stargazers_count']

    gh_url.path_parts += ('tags',)
    tags_url = gh_url.to_text()
    tags_data = _get_gh_json(tags_url)
    vtags_data = [td for td in tags_data if match_zv_tag(td['name'], PREFIXES)]
    ret['release_count'] = len(vtags_data)

    first_release = vtags_data[-1]
    first_release_data = _get_gh_rel_data(first_release)
    for k, v in first_release_data.items():
        ret['first_release_%s' % k] = v

    latest_release = vtags_data[0]
    latest_release_data = _get_gh_rel_data(latest_release)
    for k, v in latest_release_data.items():
        ret['latest_release_%s' % k] = v

    zv_releases = [rel for rel in vtags_data
                   if match_zv_tag(rel['name'], PREFIXES).group('major') == '0']
    print ' .. %s releases, %s 0ver' % (ret['release_count'], len(zv_releases))

    is_zerover = zv_releases[0] == latest_release

    ret['is_zerover'] = is_zerover

    if is_zerover:
        return ret

    last_zv_release = zv_releases[0]
    last_zv_release_data = _get_gh_rel_data(last_zv_release)

    for k, v in last_zv_release_data.items():
        ret['last_zv_release_%s' % k] = v

    return ret


def _json_default(obj):
    # yaml likes to parse some dates
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("%r is not serializable" % obj)


def _main():
    start_time = time.time()
    with open('projects.yaml') as f:
        projects = yaml.load(f)['projects']

    entries = []

    for p in projects:
        print 'processing', p['name']
        info = dict(p)
        if p.get('skip'):
            continue

        info['url'] = p.get('url', p.get('gh_url'))

        if p.get('gh_url'):
            gh_info = get_gh_project_info(p['gh_url'])
            info.update(gh_info)

        if p.get('alumnus'):
            info['is_zerover'] = p.get('is_zerover', False)
        else:
            info['is_zerover'] = True

        entries.append(info)

    from pprint import pprint

    pprint(entries)

    res = {'projects': entries,
           'gen_date': datetime.datetime.utcnow().isoformat(),
           'gen_duration': time.time() - start_time}

    with atomic_save('projects.json') as f:
        f.write(json.dumps(res, indent=2, sort_keys=True, default=_json_default))

    return


if __name__ == '__main__':
    try:
        sys.exit(_main() or 0)
    except Exception as e:
        print(' !! debugging unexpected %r' % e)
        import pdb;pdb.post_mortem()
        raise
