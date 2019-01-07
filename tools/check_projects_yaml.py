
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


def main():
    with open('projects.yaml') as f:
        data = yaml.load(f)
    IN_SCHEMA.validate(data)
    print 'projects.yaml validated'


if __name__ == '__main__':
    main()
