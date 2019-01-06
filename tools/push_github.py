
import os
from subprocess import check_call


AUTOCOMMIT_LOGIN = os.getenv('GH_TOKEN', '')
AUTOCOMMIT_EMAIL = os.getenv('AUTOCOMMIT_EMAIL', 'travis@travis-ci.org')
AUTOCOMMIT_NAME = os.getenv('AUTOCOMMIT_NAME', 'Travis CI')
AUTOCOMMIT_BRANCH = os.getenv('AUTOCOMMIT_BRANCH', os.getenv('TRAVIS_BRANCH'))
AUTOCOMMIT_TARGET = os.getenv('AUTOCOMMIT_TARGET', '.')
AUTOCOMMIT_PREFIX = os.getenv('AUTOCOMMIT_PREFIX', 'CI autocommit')

'''TRAVIS_JOB_WEB_URL'''

def call(args):
    print(args)
    ret = check_call(args)
    print(ret)
    return ret


def main():
    call(['git', 'config', '--global', 'user.email', AUTOCOMMIT_EMAIL])
    call(['git', 'config', '--global', 'user.name', AUTOCOMMIT_NAME])

    # TODO: check which remote/branch are default
    # call(['git', 'checkout', '-b', AUTOCOMMIT_BRANCH])

    call(['git', 'add', AUTOCOMMIT_TARGET])
    call(['git', 'commit', '--message', AUTOCOMMIT_PREFIX + ': ' + os.getenv('TRAVIS_JOB_WEB_URL')])

    call(['git', 'remote', 'add', 'origin-autocommit', 'https://%s@github.com/mahmoud/zerover.git' % AUTOCOMMIT_LOGIN])  # TODO
    call(['git', 'push', '--set-upstream', 'origin-autocommit', AUTOCOMMIT_BRANCH])

    return


if __name__ == '__main__':
    main()
