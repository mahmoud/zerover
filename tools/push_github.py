
import os
from subprocess import check_output, CalledProcessError


AUTOCOMMIT_LOGIN = os.getenv('GH_TOKEN', '')
AUTOCOMMIT_EMAIL = os.getenv('AUTOCOMMIT_EMAIL', 'travis@travis-ci.org')
AUTOCOMMIT_NAME = os.getenv('AUTOCOMMIT_NAME', 'Travis CI')
AUTOCOMMIT_BRANCH = os.getenv('AUTOCOMMIT_BRANCH', os.getenv('TRAVIS_BRANCH'))
AUTOCOMMIT_TARGET = os.getenv('AUTOCOMMIT_TARGET', '.')
AUTOCOMMIT_PREFIX = os.getenv('AUTOCOMMIT_PREFIX', 'CI autocommit')
AUTOCOMMIT_CANONICAL_REPO = os.getenv('AUTOCOMMIT_CANONICAL_REPO',
                                      'https://github.com/mahmoud/zerover.git')


def call(args):
    args = [unicode(a) for a in args]
    print(['$'] + args)
    ret = check_output(args)
    print(ret)
    return ret


def checkout_or_create(branch_name):
    try:
        return call(['git', 'checkout', branch_name])
    except CalledProcessError:
        return call(['git', 'checkout', '-b', branch_name])


def main():
    branch_name = AUTOCOMMIT_BRANCH
    if not branch_name:
        raise RuntimeError('expected AUTOCOMMIT_BRANCH env var to be set')
    remote_url = call(['git', 'remote', 'get-url', '--push', 'origin']).strip()
    if not remote_url.startswith('https'):
        raise RuntimeError('expected HTTPS git remote url, not %r' % remote_url)
    if remote_url != AUTOCOMMIT_CANONICAL_REPO:
        print('only committing back to canonical repo (%r), not %r' % (AUTOCOMMIT_CANONICAL_REPO, remote_url))

    call(['git', 'config', '--global', 'user.email', AUTOCOMMIT_EMAIL])
    call(['git', 'config', '--global', 'user.name', AUTOCOMMIT_NAME])

    # see default remotes
    call(['git', 'remote', '-v'])
    checkout_or_create(branch_name)

    call(['git', 'add', AUTOCOMMIT_TARGET])
    call(['git', 'commit', '--message', '%s: %s [skip ci]' % (AUTOCOMMIT_PREFIX, os.getenv('TRAVIS_JOB_WEB_URL'))])

    call(['git', 'remote', 'add', 'origin-autocommit', 'https://%s@github.com/mahmoud/zerover.git' % AUTOCOMMIT_LOGIN])  # TODO
    call(['git', 'push', '--set-upstream', 'origin-autocommit', branch_name])

    return


if __name__ == '__main__':
    main()
