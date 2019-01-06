
import os
from subprocess import check_call, CalledProcessError


AUTOCOMMIT_LOGIN = os.getenv('GH_TOKEN', '')
AUTOCOMMIT_EMAIL = os.getenv('AUTOCOMMIT_EMAIL', 'travis@travis-ci.org')
AUTOCOMMIT_NAME = os.getenv('AUTOCOMMIT_NAME', 'Travis CI')
AUTOCOMMIT_BRANCH = os.getenv('AUTOCOMMIT_BRANCH', os.getenv('TRAVIS_BRANCH'))
AUTOCOMMIT_TARGET = os.getenv('AUTOCOMMIT_TARGET', '.')
AUTOCOMMIT_PREFIX = os.getenv('AUTOCOMMIT_PREFIX', 'CI autocommit')


def call(args):
    args = [unicode(a) for a in args]
    print(['$'] + args)
    ret = check_call(args)
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
    call(['git', 'config', '--global', 'user.email', AUTOCOMMIT_EMAIL])
    call(['git', 'config', '--global', 'user.name', AUTOCOMMIT_NAME])

    # see default remotes
    call(['git', 'remote', '-v'])
    checkout_or_create(branch_name)

    call(['git', 'add', AUTOCOMMIT_TARGET])
    call(['git', 'commit', '--message', AUTOCOMMIT_PREFIX + ': ' + os.getenv('TRAVIS_JOB_WEB_URL')])

    call(['git', 'remote', 'add', 'origin-autocommit', 'https://%s@github.com/mahmoud/zerover.git' % AUTOCOMMIT_LOGIN])  # TODO
    call(['git', 'push', '--set-upstream', 'origin-autocommit', branch_name])

    return


if __name__ == '__main__':
    main()
