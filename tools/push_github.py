import os
import sys
from subprocess import check_output, CalledProcessError, STDOUT

AUTOCOMMIT_LOGIN = os.getenv("GH_TOKEN", "")
AUTOCOMMIT_EMAIL = os.getenv("AUTOCOMMIT_EMAIL", "travis@travis-ci.org")
AUTOCOMMIT_NAME = os.getenv("AUTOCOMMIT_NAME", "Travis CI")
AUTOCOMMIT_BRANCH = os.getenv("AUTOCOMMIT_BRANCH", os.getenv("TRAVIS_BRANCH"))
AUTOCOMMIT_TARGET = os.getenv("AUTOCOMMIT_TARGET", ".")
AUTOCOMMIT_PREFIX = os.getenv("AUTOCOMMIT_PREFIX", "CI autocommit")
AUTOCOMMIT_CANONICAL_REPO = os.getenv(
    "AUTOCOMMIT_CANONICAL_REPO", "https://github.com/mahmoud/zerover.git"
)


def call(args: list[str]) -> str:
    print(["$"] + args)
    try:
        ret = check_output(args, stderr=STDOUT, text=True)  # Ensure text output
        print(ret)
        return ret
    except CalledProcessError as e:
        print(e.output)
        raise e


def checkout_or_create(branch_name: str) -> str:
    try:
        return call(["git", "checkout", branch_name])
    except CalledProcessError:
        return call(["git", "checkout", "-b", branch_name])


def main():
    branch_name = AUTOCOMMIT_BRANCH
    if not branch_name:
        raise RuntimeError("Expected AUTOCOMMIT_BRANCH env var to be set")

    remote_url = call(["git", "remote", "get-url", "--push", "origin"]).strip()
    if not remote_url.startswith("https"):
        raise RuntimeError(f"Expected HTTPS git remote url, not {remote_url!r}")
    if remote_url != AUTOCOMMIT_CANONICAL_REPO:
        print(
            f"Only committing back to canonical repo ({AUTOCOMMIT_CANONICAL_REPO!r}), not {remote_url!r}"
        )
        return 0
    if not call(["git", "status", "--porcelain"]).strip():
        print("Nothing to autocommit, exiting.")
        return 0

    call(["git", "config", "--global", "user.email", AUTOCOMMIT_EMAIL])
    call(["git", "config", "--global", "user.name", AUTOCOMMIT_NAME])

    # See default remotes
    call(["git", "remote", "-v"])
    checkout_or_create(branch_name)

    call(["git", "add", AUTOCOMMIT_TARGET])
    call(
        [
            "git",
            "commit",
            "--message",
            f'{AUTOCOMMIT_PREFIX}: {os.getenv("TRAVIS_JOB_WEB_URL")} [skip ci]',
        ]
    )

    call(
        [
            "git",
            "remote",
            "add",
            "origin-autocommit",
            f"https://{AUTOCOMMIT_LOGIN}@github.com/mahmoud/zerover.git",
        ]
    )
    call(["git", "push", "--set-upstream", "origin-autocommit", branch_name])

    sys.exit(0)


if __name__ == "__main__":
    main()
