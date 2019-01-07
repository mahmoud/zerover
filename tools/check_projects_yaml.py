
import sys
from collections import defaultdict

import yaml
from schema import Schema, And, Or, Optional
from hyperlink import parse


def check_url(url_str):
    url = parse(unicode(url_str))
    assert url.scheme in ('http', 'https')
    return url


IN_SCHEMA = Schema({'projects': [{'name': str,
                                  Or('url', 'gh_url'): check_url}]},
                   ignore_extra_keys=True)


def redundant(src, key=None, distinct=False, sort=True):
    """The complement of unique(), returns non-unique values. Pass
    distinct=True to get a list of the *first* redundant value for
    each key. Results are sorted by default.

    >>> redundant(range(5))
    []
    >>> redundant([1, 2, 3, 2, 3, 3])
    [[2, 2], [3, 3, 3]]
    >>> redundant([1, 2, 3, 2, 3, 3], distinct=True)
    [2, 3]
    >>> redundant(['hi', 'Hi', 'HI', 'hello'], key=str.lower)
    [['hi', 'Hi', 'HI']]
    >>> redundant(['hi', 'Hi', 'HI', 'hello'], distinct=True, key=str.lower)
    ['Hi']

    """
    if key is None:
        pass
    elif callable(key):
        key_func = key
    elif isinstance(key, basestring):
        key_func = lambda x: getattr(x, key, x)
    else:
        raise TypeError('"key" expected a string or callable, not %r' % key)
    seen = {}  # key to first seen item
    redundant_seen = {}
    for i in src:
        k = key_func(i) if key else i
        if k not in seen:
            seen[k] = i
        else:
            if k in redundant_seen:
                if not distinct:
                    redundant_seen[k].append(i)
            else:
                redundant_seen[k] = [seen[k], i]
    if distinct:
        ret = [r[1] for r in redundant_seen.values()]
    else:
        ret = redundant_seen.values()
    return sorted(ret) if sort else ret



def main():
    with open('projects.yaml') as f:
        data = yaml.load(f)
    IN_SCHEMA.validate(data)

    projects = data['projects']

    re_names = redundant([p['name'].lower() for p in projects])
    if re_names:
        print('got projects with duplicate names: %r' % re_names)
        sys.exit(1)

    re_urls = redundant([p.get('gh_url', p.get('url')) for p in projects])
    if re_urls:
        print('got projects with duplicate urls: %r' % re_urls)
        sys.exit(1)



    print 'projects.yaml validated'


if __name__ == '__main__':
    sys.exit(main() or 0)
